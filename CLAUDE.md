# DiagramGPT

Contributor notes for the local workspace. User-facing setup and runtime docs live in [`README.md`](README.md).

## Quick Start

```bash
pip install -e ".[dev]"
npm install -g @mermaid-js/mermaid-cli
python -m src.cli doctor
python -m src.cli serve
```

The app serves on `http://127.0.0.1:8500` by default unless `PORT` is overridden.

## Architecture
```
src/
  config.py            — Settings from .env (Pydantic)
  pipeline.py          — Main pipeline: description → code → render → save
  cli.py               — CLI entry point (generate, serve)
  generators/
    types.py           — DiagramType enum, auto-detection, request/result models
    prompts.py         — LLM prompt templates per diagram type
    llm.py             — Claude API integration
  renderers/
    render.py          — Mermaid CLI + D2 CLI → SVG/PNG
  styles/
    tokens.py          — Color palettes, font presets
    themes.py          — Mermaid theme config + D2 style generation
  api/
    server.py          — FastAPI endpoints
web/                   — Next.js frontend (TBD)
tests/                 — pytest tests
diagrams/              — Generated output
```

## Diagram Types
flowchart, sequence, architecture, er, class, network, mindmap, timeline, state, gantt, tree, custom

## Style Presets
professional, dark, vibrant, monochrome, network

## Env Vars
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `LLM_PROVIDER` — `auto` (default)
- `DEFAULT_STYLE` — `professional` (default)
- `DEFAULT_FONT` — `clean` (default)
- `MERMAID_CLI_PATH` — path to `mmdc` (default: `mmdc`)
- `D2_PATH` — path to `d2` (default: `d2`)

## Conventions
- Python 3.12+, ES modules for any JS
- async throughout — generators and renderers are all async
- Two-track rendering: Mermaid (primary), D2 (for network/architecture)
- Retry on render failure (LLM regenerates code)
