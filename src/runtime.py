"""Runtime status helpers shared by the API and CLI."""

from . import __version__
from .config import settings
from .generators.llm import get_llm_status
from .generators.types import DiagramType, OutputFormat
from .renderers.render import get_render_capabilities
from .styles.tokens import FONTS, PALETTES


def build_runtime_status() -> dict:
    """Return a user-facing snapshot of configured providers and local tools."""
    llm = get_llm_status()
    renderers = get_render_capabilities()
    available_formats = []

    if renderers["mermaid"]["available"]:
        available_formats.append(OutputFormat.MERMAID.value)
    if renderers["d2"]["available"]:
        available_formats.append(OutputFormat.D2.value)

    ready = llm["ready"] and bool(available_formats)

    return {
        "name": "DiagramGPT",
        "version": __version__,
        "ready": ready,
        "defaults": {
            "provider": settings.llm_provider,
            "style": settings.default_style,
            "font": settings.default_font,
            "host": settings.host,
            "port": settings.port,
        },
        "limits": {
            "max_description_length": settings.max_description_length,
            "diagram_width": {
                "min": settings.min_diagram_width,
                "max": settings.max_diagram_width,
            },
            "diagram_height": {
                "min": settings.min_diagram_height,
                "max": settings.max_diagram_height,
            },
        },
        "llm": llm,
        "renderers": renderers,
        "available_formats": available_formats,
        "supported_uploads": [".csv", ".json", ".xlsx", ".txt", ".md"],
        "styles": list(PALETTES.keys()),
        "fonts": list(FONTS.keys()),
        "types": [diagram_type.value for diagram_type in DiagramType],
    }
