"""CLI entry point for DiagramGPT."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .config import settings
from .data_sources import combine_summaries, summarize_path
from .generators.llm import ProviderConfigurationError
from .generators.types import DiagramRequest, DiagramType, OutputFormat
from .pipeline import DiagramRequestValidationError, generate_diagram, save_diagram
from .runtime import build_runtime_status


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="diagramgpt",
        description="Generate diagrams from natural language descriptions",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Generate command
    gen = subparsers.add_parser("generate", aliases=["gen", "g"], help="Generate a diagram")
    gen.add_argument("description", help="Natural language description of the diagram")
    gen.add_argument(
        "--type",
        "-t",
        choices=[t.value for t in DiagramType],
        help="Diagram type (auto-detected if omitted)",
    )
    gen.add_argument(
        "--style",
        "-s",
        default=settings.default_style,
        help="Style preset (professional, dark, vibrant, monochrome, network)",
    )
    gen.add_argument(
        "--format",
        "-f",
        default="mermaid",
        choices=["mermaid", "d2"],
        help="Output format",
    )
    gen.add_argument("--output", "-o", help="Output filename (without extension)")
    gen.add_argument("--width", "-w", type=int, default=1200)
    gen.add_argument("--height", type=int, default=800)
    gen.add_argument("--font", default=settings.default_font, help="Font preset")
    gen.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="Attach a local CSV, JSON, XLSX, TXT, or MD file as diagram context",
    )

    # Serve command
    serve = subparsers.add_parser("serve", help="Start the API server")
    serve.add_argument("--host", default=settings.host)
    serve.add_argument("--port", "-p", type=int, default=settings.port)
    serve.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for local development",
    )

    doctor = subparsers.add_parser("doctor", help="Show provider and renderer readiness")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable status")

    args = parser.parse_args()

    if args.command in ("generate", "gen", "g"):
        return asyncio.run(_generate(args))
    if args.command == "serve":
        _serve(args)
        return 0
    if args.command == "doctor":
        return _doctor(args)

    parser.print_help()
    return 1


async def _generate(args) -> int:
    diagram_type = DiagramType(args.type) if args.type else None
    output_format = OutputFormat(args.format)

    data_context = ""
    if args.context_file:
        summaries = [summarize_path(Path(path)) for path in args.context_file]
        data_context = combine_summaries(summaries)

    request = DiagramRequest(
        description=args.description,
        diagram_type=diagram_type,
        data_context=data_context,
        style=args.style,
        font=args.font,
        output_format=output_format,
        width=args.width,
        height=args.height,
    )

    try:
        print(f"Generating {diagram_type or 'auto-detected'} diagram...")
        result = await generate_diagram(request)
    except (DiagramRequestValidationError, ProviderConfigurationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if result.metadata and result.metadata.get("retries_exhausted"):
        print(f"Warning: Render failed — {result.metadata.get('error')}", file=sys.stderr)
        print("Source code generated but could not be rendered.")

    path = await save_diagram(result, name=args.output)
    print(f"Saved to: {path}")
    print(f"Source code:\n{result.source_code}")
    return 0 if result.svg else 2


def _serve(args):
    import uvicorn

    uvicorn.run("src.api.server:app", host=args.host, port=args.port, reload=args.reload)


def _doctor(args) -> int:
    status = build_runtime_status()
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"DiagramGPT {status['version']}")
        print(f"Ready: {'yes' if status['ready'] else 'no'}")
        print(
            "Provider: "
            f"{status['llm']['resolved_provider'] or status['llm']['configured_provider']}"
        )
        if status["llm"]["error"]:
            print(f"LLM issue: {status['llm']['error']}")
        print(
            "Renderers: "
            f"Mermaid={'yes' if status['renderers']['mermaid']['available'] else 'no'}, "
            f"D2={'yes' if status['renderers']['d2']['available'] else 'no'}"
        )
    return 0 if status["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
