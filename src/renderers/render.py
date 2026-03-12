"""Render diagram code to SVG/PNG using external tools."""

import asyncio
import contextlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from ..config import settings
from ..generators.types import DiagramResult, DiagramType, OutputFormat
from ..styles.themes import mermaid_theme_config

MERMAID_SUBGRAPH_PATTERN = re.compile(
    r"^(\s*subgraph\s+)([A-Za-z_][\w]*?)\[(.+?)\](\s*)$",
    re.MULTILINE,
)
MERMAID_NODE_LABEL_PATTERN = re.compile(r"(\b[A-Za-z_][\w]*)\[(.+?)\]")
D2_CONTAINER_PATTERN = re.compile(r"^(\s*)container\s+([A-Za-z_][\w]*)\s*\{\s*$")
D2_NODE_PATTERN = re.compile(r"^(\s*)([A-Za-z_][\w]*)\[(.+?)\]\s*$")
D2_EDGE_PATTERN = re.compile(
    r'^(\s*)([A-Za-z_][\w]*)\s*-->\s*([A-Za-z_][\w]*)\s*\[label:\s*"?(.*?)"?\]\s*$'
)


def normalize_mermaid_code(code: str) -> str:
    """Apply low-risk Mermaid syntax cleanup before rendering."""
    code = MERMAID_SUBGRAPH_PATTERN.sub(r'\1\2["\3"]\4', code)

    normalized_lines = []
    for line in code.splitlines():
        if line.lstrip().startswith("subgraph "):
            normalized_lines.append(line)
            continue
        normalized_lines.append(MERMAID_NODE_LABEL_PATTERN.sub(r'\1["\2"]', line))

    return "\n".join(normalized_lines)


def normalize_d2_code(code: str) -> str:
    """Convert common pseudo-D2 output into valid D2 syntax."""
    normalized_lines = []

    for line in code.splitlines():
        container_match = D2_CONTAINER_PATTERN.match(line)
        if container_match:
            indent, identifier = container_match.groups()
            normalized_lines.append(
                f'{indent}{identifier}: "{_humanize_identifier(identifier)}" {{'
            )
            continue

        node_match = D2_NODE_PATTERN.match(line)
        if node_match:
            indent, identifier, label = node_match.groups()
            normalized_lines.append(f'{indent}{identifier}: "{label}"')
            continue

        edge_match = D2_EDGE_PATTERN.match(line)
        if edge_match:
            indent, source, target, label = edge_match.groups()
            normalized_lines.append(f'{indent}{source} -> {target}: "{label}"')
            continue

        normalized_lines.append(line.replace("-->", "->"))

    return "\n".join(normalized_lines)


def _humanize_identifier(identifier: str) -> str:
    """Turn a camelCase or snake_case identifier into a readable label."""
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier).replace("_", " ")
    return words.strip().title()


def _resolve_cmd(name: str) -> str | None:
    """Resolve a command name to its full path, handling Windows .cmd/.bat extensions."""
    candidate = Path(name)
    if candidate.exists():
        return str(candidate)

    resolved = shutil.which(name)
    if resolved:
        return resolved
    if sys.platform == "win32":
        for ext in (".cmd", ".bat", ".exe"):
            resolved = shutil.which(name + ext)
            if resolved:
                return resolved
        common_windows_paths = [
            Path("C:/Program Files/D2/d2.exe"),
            Path("C:/Program Files/D2/bin/d2.exe"),
        ]
        for path in common_windows_paths:
            if path.exists() and (name.lower() == "d2" or Path(name).name.lower() == "d2.exe"):
                return str(path)
    return None


def get_render_capabilities() -> dict:
    """Return safe renderer diagnostics for status and doctor commands."""
    mermaid_path = _resolve_cmd(settings.mermaid_cli_path)
    d2_path = _resolve_cmd(settings.d2_path)
    png_status = {
        "available": bool(mermaid_path),
        "engine": "mermaid-cli",
        "error": None if mermaid_path else "mermaid-cli is required for PNG export",
    }

    return {
        "mermaid": {
            "available": bool(mermaid_path),
            "path": mermaid_path,
        },
        "d2": {
            "available": bool(d2_path),
            "path": d2_path,
        },
        "png_export": png_status,
    }


async def _communicate_with_timeout(
    proc: asyncio.subprocess.Process,
    label: str,
) -> tuple[bytes, bytes]:
    """Wait on a subprocess with a hard timeout and clean termination."""
    try:
        return await asyncio.wait_for(proc.communicate(), timeout=settings.render_timeout_seconds)
    except asyncio.TimeoutError as exc:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
        await proc.communicate()
        raise RenderError(
            f"{label} render timed out after {settings.render_timeout_seconds} seconds."
        ) from exc


async def render_mermaid(
    code: str,
    diagram_type: DiagramType,
    palette: str = "professional",
    font: str = "clean",
    width: int = 1200,
    height: int = 800,
) -> DiagramResult:
    """Render Mermaid code to SVG using mermaid-cli (mmdc)."""
    theme = mermaid_theme_config(palette, font)
    mmdc = _resolve_cmd(settings.mermaid_cli_path)

    if not mmdc:
        raise RenderError(
            "Mermaid renderer is not available. Install mermaid-cli or set MERMAID_CLI_PATH."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.mmd"
        output_file = Path(tmpdir) / "output.svg"
        config_file = Path(tmpdir) / "config.json"

        input_file.write_text(code, encoding="utf-8")
        config_file.write_text(json.dumps(theme), encoding="utf-8")

        cmd = [
            mmdc,
            "-i", str(input_file),
            "-o", str(output_file),
            "-c", str(config_file),
            "-w", str(width),
            "-H", str(height),
            "-b", "transparent",
            "--pdfFit",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await _communicate_with_timeout(proc, "Mermaid")

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown render error"
            raise RenderError(f"Mermaid render failed: {error_msg}", code=code)

        svg_content = output_file.read_text(encoding="utf-8")

    return DiagramResult(
        source_code=code,
        output_format=OutputFormat.MERMAID,
        diagram_type=diagram_type,
        svg=svg_content,
    )


async def render_mermaid_png(
    code: str,
    palette: str = "professional",
    font: str = "clean",
    width: int = 1200,
    height: int = 800,
) -> bytes:
    """Render Mermaid code directly to PNG using mermaid-cli."""
    theme = mermaid_theme_config(palette, font)
    mmdc = _resolve_cmd(settings.mermaid_cli_path)

    if not mmdc:
        raise RenderError(
            "PNG export is not available because mermaid-cli is not installed.",
            code=code,
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.mmd"
        output_file = Path(tmpdir) / "output.png"
        config_file = Path(tmpdir) / "config.json"

        input_file.write_text(code, encoding="utf-8")
        config_file.write_text(json.dumps(theme), encoding="utf-8")

        cmd = [
            mmdc,
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "-c",
            str(config_file),
            "-w",
            str(width),
            "-H",
            str(height),
            "-b",
            "transparent",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await _communicate_with_timeout(proc, "Mermaid PNG")

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown render error"
            raise RenderError(f"Mermaid PNG export failed: {error_msg}", code=code)

        return output_file.read_bytes()


async def render_d2(
    code: str,
    diagram_type: DiagramType,
    palette: str = "professional",
) -> DiagramResult:
    """Render D2 code to SVG using the d2 CLI."""
    d2 = _resolve_cmd(settings.d2_path)
    if not d2:
        raise RenderError("D2 renderer is not available. Install d2 or set D2_PATH.", code=code)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.d2"
        output_file = Path(tmpdir) / "output.svg"

        input_file.write_text(code, encoding="utf-8")

        # D2 theme mapping
        d2_themes = {
            "professional": "0",
            "dark": "200",
            "vibrant": "1",
            "monochrome": "300",
            "network": "0",
        }
        theme_id = d2_themes.get(palette, "0")

        cmd = [
            d2,
            "--theme", theme_id,
            "--layout", "elk",
            str(input_file),
            str(output_file),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await _communicate_with_timeout(proc, "D2")

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown render error"
            raise RenderError(f"D2 render failed: {error_msg}", code=code)

        svg_content = output_file.read_text(encoding="utf-8")

    return DiagramResult(
        source_code=code,
        output_format=OutputFormat.D2,
        diagram_type=diagram_type,
        svg=svg_content,
    )


async def svg_to_png(svg_content: str, width: int = 1200, scale: int = 2) -> bytes:
    """Convert SVG string to PNG bytes using CairoSVG."""
    try:
        import cairosvg
    except (ImportError, OSError) as exc:
        raise RenderError(
            "PNG export is not available. Install the Cairo runtime to enable PNG rendering."
        ) from exc

    return cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        output_width=width * scale,
    )


class RenderError(Exception):
    """Raised when diagram rendering fails."""

    def __init__(self, message: str, code: str = ""):
        self.code = code
        super().__init__(message)
