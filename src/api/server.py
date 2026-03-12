"""FastAPI server for DiagramGPT."""

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field, field_validator

from .. import __version__
from ..config import settings
from ..data_sources import DataSourceError, combine_summaries, summarize_file_bytes
from ..generators.llm import ProviderConfigurationError
from ..generators.types import DiagramRequest, DiagramType, OutputFormat
from ..pipeline import DiagramRequestValidationError, generate_diagram, save_diagram
from ..renderers.render import RenderError, render_mermaid_png, svg_to_png
from ..runtime import build_runtime_status
from ..styles.tokens import FONTS, PALETTES

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DiagramGPT",
    description="Generate publication-ready diagrams from natural language",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.normalized_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    description: str = Field(min_length=4, max_length=settings.max_description_length)
    diagram_type: DiagramType | None = None
    data_context: str = Field(default="", max_length=settings.max_data_context_length)
    style: str = settings.default_style
    font: str = settings.default_font
    output_format: OutputFormat = OutputFormat.MERMAID
    width: int = Field(default=1200, ge=settings.min_diagram_width, le=settings.max_diagram_width)
    height: int = Field(
        default=800,
        ge=settings.min_diagram_height,
        le=settings.max_diagram_height,
    )

    @field_validator("style")
    @classmethod
    def validate_style(cls, value: str) -> str:
        if value not in PALETTES:
            raise ValueError(f"Unknown style '{value}'.")
        return value

    @field_validator("font")
    @classmethod
    def validate_font(cls, value: str) -> str:
        if value not in FONTS:
            raise ValueError(f"Unknown font '{value}'.")
        return value


class GenerateResponse(BaseModel):
    source_code: str
    diagram_type: str
    output_format: str
    svg: str | None = None
    error: str | None = None


class UploadSummary(BaseModel):
    filename: str
    file_type: str
    summary: str
    suggested_diagram_types: list[str]


class UploadResponse(BaseModel):
    files: list[UploadSummary]
    combined_context: str
    suggested_diagram_types: list[str]


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generate a diagram from a natural language description."""
    try:
        request = DiagramRequest(
            description=req.description,
            diagram_type=req.diagram_type,
            data_context=req.data_context,
            style=req.style,
            font=req.font,
            output_format=req.output_format,
            width=req.width,
            height=req.height,
        )

        result = await generate_diagram(request)

        error = None
        if result.metadata and result.metadata.get("retries_exhausted"):
            error = result.metadata.get("error", "Render failed after retries")

        if result.svg and settings.auto_save:
            await save_diagram(result)

        return GenerateResponse(
            source_code=result.source_code,
            diagram_type=result.diagram_type.value,
            output_format=result.output_format.value,
            svg=result.svg,
            error=error,
        )
    except DiagramRequestValidationError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except ProviderConfigurationError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except RenderError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        request_id = uuid4().hex[:8]
        logger.exception("Unexpected generate failure [%s]", request_id)
        raise HTTPException(
            500,
            detail=f"Diagram generation failed. Reference code: {request_id}.",
        ) from exc


@app.post("/api/render/png")
async def render_png(req: GenerateRequest):
    """Generate a diagram and return as PNG."""
    try:
        request = DiagramRequest(
            description=req.description,
            diagram_type=req.diagram_type,
            data_context=req.data_context,
            style=req.style,
            font=req.font,
            output_format=req.output_format,
            width=req.width,
            height=req.height,
        )

        result = await generate_diagram(request)
        if not result.svg:
            raise HTTPException(503, "The diagram could not be rendered to SVG.")

        if req.output_format == OutputFormat.MERMAID:
            png_bytes = await render_mermaid_png(
                result.source_code,
                palette=req.style,
                font=req.font,
                width=req.width,
                height=req.height,
            )
        else:
            png_bytes = await svg_to_png(result.svg, width=req.width)
        return Response(content=png_bytes, media_type="image/png")
    except DiagramRequestValidationError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except ProviderConfigurationError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except RenderError as exc:
        raise HTTPException(503, detail=str(exc)) from exc


@app.get("/api/styles")
async def list_styles():
    """List available style presets."""
    return {
        "palettes": list(PALETTES.keys()),
        "fonts": list(FONTS.keys()),
    }


@app.get("/api/types")
async def list_types():
    """List available diagram types."""
    return {"types": [t.value for t in DiagramType]}


@app.post("/api/context/upload", response_model=UploadResponse)
async def upload_context(files: list[UploadFile] = File(...)):
    """Summarize uploaded data files into prompt context."""
    try:
        summaries = []
        for upload in files:
            content = await upload.read()
            summaries.append(
                summarize_file_bytes(
                    upload.filename or "upload",
                    content,
                    media_type=upload.content_type,
                )
            )
        suggested_types = sorted(
            {diagram_type for item in summaries for diagram_type in item["suggested_diagram_types"]}
        )
        return UploadResponse(
            files=[UploadSummary(**item) for item in summaries],
            combined_context=combine_summaries(summaries),
            suggested_diagram_types=suggested_types,
        )
    except DataSourceError as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__}


@app.get("/api/status")
async def status():
    """Return current provider and renderer availability."""
    return build_runtime_status()


@app.get("/ready")
async def ready():
    payload = build_runtime_status()
    status_code = 200 if payload["ready"] else 503
    return JSONResponse(payload, status_code=status_code)


# Serve web UI
WEB_DIR = Path(__file__).parent.parent.parent / "web"


@app.get("/")
async def serve_ui():
    return FileResponse(WEB_DIR / "index.html")
