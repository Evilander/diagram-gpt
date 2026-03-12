# DiagramGPT

DiagramGPT turns natural-language prompts into publication-ready Mermaid and D2 diagrams, with a local web UI, FastAPI service, CLI, PNG export, and structured data-file uploads for grounded charts and diagrams.

## Quick Start

```bash
pip install -e ".[dev]"
npm install -g @mermaid-js/mermaid-cli
python -m src.cli doctor
python -m src.cli serve
```

Then open `http://127.0.0.1:8500`.

## What It Ships

- Natural-language diagram generation for flowcharts, sequence diagrams, architecture views, ERDs, class diagrams, mind maps, timelines, state machines, gantt charts, trees, and network diagrams
- Mermaid chart generation for pie and XY-style chart prompts
- Mermaid rendering through `mmdc` and optional D2 rendering when `d2` is installed
- FastAPI endpoints for generation, PNG export, styles, types, health, and readiness
- Data-file upload support for `.csv`, `.json`, `.xlsx`, `.txt`, and `.md` context
- A browser UI that reflects runtime capability state instead of failing silently
- A CLI with `generate`, `serve`, and `doctor` commands

## Release Highlights

- Runtime capability checks for Mermaid, D2, provider readiness, and PNG export
- Web upload flow for CSV, JSON, XLSX, TXT, and Markdown grounding
- Mermaid-native PNG rendering path for reliable exports
- CLI `--context-file` support for data-backed generation without the browser
- FastAPI `/api/status` and `/ready` endpoints for deploy and health checks

## Requirements

- Python 3.11+
- Node.js if you want Mermaid SVG rendering through `@mermaid-js/mermaid-cli`
- Optional: the `d2` CLI if you want D2 output
- One LLM provider key:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`

## Setup

```bash
pip install -e ".[dev]"
npm install -g @mermaid-js/mermaid-cli
```

Optional D2 support:

```bash
d2 --version
```

On Windows, a working install path is:

```powershell
winget install --id Terrastruct.D2 -e
```

If `d2` is not installed, DiagramGPT will still run, but D2 output will stay unavailable and `/ready` will report the reduced capability set.

## Release Artifacts

Packaged release builds are produced with:

```bash
python -m build
```

This generates a wheel and source distribution under `dist/`, which are suitable for attaching to GitHub releases.

## Credentials

Set one provider key in your shell before running live generation:

```powershell
$env:OPENAI_API_KEY = "your-openai-key"
```

or:

```powershell
$env:ANTHROPIC_API_KEY = "your-anthropic-key"
```

`LLM_PROVIDER=openai` is the checked-in default. Switch it to `auto` or `claude` if that matches your environment better.

## CLI

Check readiness first:

```bash
python -m src.cli doctor
python -m src.cli doctor --json
```

Generate a diagram:

```bash
python -m src.cli generate "user signup flow with email verification"
python -m src.cli generate "network topology with 3 subnets behind a firewall" --type network --style network
python -m src.cli generate "event-driven microservice architecture" --type architecture --format d2
python -m src.cli generate "Create a chart showing monthly revenue trend" --type chart --context-file tests/fixtures/revenue.csv
```

Run the API and web UI:

```bash
python -m src.cli serve
```

The app listens on `http://127.0.0.1:8500` by default unless `PORT` is overridden.

## Example Workflows

Generate a Mermaid chart from a CSV:

```bash
python -m src.cli generate "Create a chart showing monthly revenue trend" --type chart --context-file tests/fixtures/revenue.csv
```

Generate a D2 architecture diagram:

```bash
python -m src.cli generate "event-driven microservice architecture with api gateway and worker queue" --type architecture --format d2
```

## API

- `GET /`
- `POST /api/generate`
- `POST /api/render/png`
- `POST /api/context/upload`
- `GET /api/styles`
- `GET /api/types`
- `GET /api/health`
- `GET /api/status`
- `GET /ready`

Example request:

```bash
curl -X POST http://127.0.0.1:8500/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"description\":\"login flow between browser, api, and database\"}"
```

Upload data files as multipart form data:

```bash
curl -X POST http://127.0.0.1:8500/api/context/upload ^
  -F "files=@tests/fixtures/revenue.csv"
```

## Configuration

Environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `LLM_PROVIDER` (`auto`, `openai`, `claude`)
- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`
- `DEFAULT_STYLE`
- `DEFAULT_FONT`
- `MERMAID_CLI_PATH`
- `D2_PATH`
- `HOST`
- `PORT`
- `ALLOWED_ORIGINS`
- `OUTPUT_DIR`
- `MAX_DESCRIPTION_LENGTH`
- `MIN_DIAGRAM_WIDTH`
- `MAX_DIAGRAM_WIDTH`
- `MIN_DIAGRAM_HEIGHT`
- `MAX_DIAGRAM_HEIGHT`
- `LLM_TIMEOUT_SECONDS`
- `RENDER_TIMEOUT_SECONDS`
- `AUTO_SAVE`

## Uploads And Charts

- Upload CSV, JSON, XLSX, TXT, or Markdown files in the web UI to ground diagram generation.
- Use `--context-file` in the CLI to attach the same kinds of files without the browser.
- Choose `chart` explicitly when you want Mermaid chart output, or leave type on auto-detect and describe the chart you want.
- Use `/api/context/upload` when integrating uploads into another client.

## Verification

```bash
python -m pytest -q
python -m ruff check .
python -m compileall src tests
python -m build
```
