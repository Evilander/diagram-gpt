"""Main diagram generation pipeline: description → code → render → output."""

import hashlib
import re
from datetime import datetime
from pathlib import Path

from .config import settings
from .generators.llm import fix_diagram_code, generate_diagram_code
from .generators.types import (
    DiagramRequest,
    DiagramResult,
    OutputFormat,
    detect_diagram_type,
)
from .renderers.render import (
    RenderError,
    normalize_d2_code,
    normalize_mermaid_code,
    render_d2,
    render_mermaid,
    svg_to_png,
)
from .styles.tokens import FONTS, PALETTES

MAX_RETRIES = 2
SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class DiagramRequestValidationError(ValueError):
    """Raised when a request cannot be processed safely."""


def validate_request(request: DiagramRequest) -> None:
    """Validate user-controlled request fields used by the CLI and API."""
    description = request.description.strip()
    if not description:
        raise DiagramRequestValidationError("Description cannot be empty.")
    if len(description) > settings.max_description_length:
        raise DiagramRequestValidationError(
            f"Description is too long. Limit is {settings.max_description_length} characters."
        )
    if len(request.data_context) > settings.max_data_context_length:
        raise DiagramRequestValidationError(
            "Uploaded data context is too long. "
            f"Limit is {settings.max_data_context_length} characters."
        )
    if request.style not in PALETTES:
        raise DiagramRequestValidationError(
            f"Unknown style '{request.style}'. Choose from: {', '.join(PALETTES)}."
        )
    if request.font not in FONTS:
        raise DiagramRequestValidationError(
            f"Unknown font '{request.font}'. Choose from: {', '.join(FONTS)}."
        )
    if not settings.min_diagram_width <= request.width <= settings.max_diagram_width:
        raise DiagramRequestValidationError(
            f"Width must be between {settings.min_diagram_width} and "
            f"{settings.max_diagram_width}px."
        )
    if not settings.min_diagram_height <= request.height <= settings.max_diagram_height:
        raise DiagramRequestValidationError(
            f"Height must be between {settings.min_diagram_height} and "
            f"{settings.max_diagram_height}px."
        )


def should_retry_render_error(error: RenderError) -> bool:
    """Retry syntax-like failures, not missing binaries or timeouts."""
    non_retry_markers = (
        "not available",
        "timed out",
        "install",
        "required",
        "No API key configured",
    )
    return not any(marker.lower() in str(error).lower() for marker in non_retry_markers)


def sanitize_output_name(name: str | None, result: DiagramResult) -> str:
    """Collapse user-provided names to safe filenames within the output directory."""
    if not name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        code_hash = hashlib.blake2s(result.source_code.encode("utf-8"), digest_size=3).hexdigest()
        return f"{result.diagram_type.value}_{timestamp}_{code_hash}"

    candidate = Path(name).name
    candidate = SAFE_NAME_PATTERN.sub("-", candidate).strip(" .-_")
    if not candidate:
        raise DiagramRequestValidationError("Output filename must contain letters or numbers.")
    return candidate[:80]


async def generate_diagram(request: DiagramRequest) -> DiagramResult:
    """Full pipeline: description → detect type → generate code → render → result."""
    validate_request(request)
    diagram_type = request.diagram_type or detect_diagram_type(request.description)
    output_format = request.output_format

    # Generate initial code
    code = await generate_diagram_code(
        description=request.description,
        diagram_type=diagram_type,
        output_format=output_format,
        data_context=request.data_context,
    )
    if output_format == OutputFormat.MERMAID:
        code = normalize_mermaid_code(code)
    elif output_format == OutputFormat.D2:
        code = normalize_d2_code(code)

    # Try to render, with error-fed retries
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            if output_format == OutputFormat.D2:
                result = await render_d2(
                    code=code,
                    diagram_type=diagram_type,
                    palette=request.style,
                )
            else:
                result = await render_mermaid(
                    code=code,
                    diagram_type=diagram_type,
                    palette=request.style,
                    font=request.font,
                    width=request.width,
                    height=request.height,
                )
            return result

        except RenderError as e:
            last_error = e
            if attempt < MAX_RETRIES and should_retry_render_error(e):
                # Feed the error back to the LLM so it can fix the code
                code = await fix_diagram_code(
                    original_code=code,
                    error_message=str(e),
                    output_format=output_format,
                )
                if output_format == OutputFormat.MERMAID:
                    code = normalize_mermaid_code(code)
                elif output_format == OutputFormat.D2:
                    code = normalize_d2_code(code)

    # All retries exhausted — return the code without rendered output
    return DiagramResult(
        source_code=code,
        output_format=output_format,
        diagram_type=diagram_type,
        metadata={"error": str(last_error), "retries_exhausted": True},
    )


async def save_diagram(result: DiagramResult, name: str | None = None) -> Path:
    """Save a rendered diagram to the output directory."""
    base = settings.output_dir / sanitize_output_name(name, result)

    # Save source code
    ext = ".mmd" if result.output_format == OutputFormat.MERMAID else ".d2"
    source_path = base.with_suffix(ext)
    source_path.write_text(result.source_code, encoding="utf-8")

    # Save SVG
    if result.svg:
        svg_path = base.with_suffix(".svg")
        svg_path.write_text(result.svg, encoding="utf-8")

        # Save PNG
        try:
            png_bytes = await svg_to_png(result.svg)
            png_path = base.with_suffix(".png")
            png_path.write_bytes(png_bytes)
        except Exception:
            pass  # CairoSVG not available — skip PNG

    return source_path
