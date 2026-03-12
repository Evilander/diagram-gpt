# DiagramGPT — Handoff

## Getting Started

### Prerequisites
- Python 3.12+, Node.js 20+
- mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`)
- D2 language (`curl -fsSL https://d2lang.com/install.sh | sh`)
- LLM API key (Claude or OpenAI) or local model

### Phase 1: Text → Mermaid/D2 (Week 1)
1. Build prompt templates for common diagram types:
   - System architecture diagrams
   - Sequence diagrams
   - Flowcharts
   - Entity relationship diagrams
   - Class diagrams
   - Network topologies
2. Text → LLM → Mermaid/D2 code → render → SVG/PNG
3. Add validation: parse generated code before rendering, retry on syntax errors
4. Test with 50+ natural language descriptions

### Phase 2: Style System (Week 2)
1. Define design tokens:
   - Color palettes: professional, vibrant, monochrome, dark mode
   - Font presets: clean (Inter), technical (JetBrains Mono), academic (Computer Modern)
   - Layout presets: compact, spacious, presentation
2. Apply styles via Mermaid themes / D2 styles / CSS overrides
3. Brand customization: user-defined colors, logos, fonts

### Phase 3: Web App (Week 2-3)
1. Next.js frontend:
   - Natural language input with diagram type selector
   - Live preview (re-renders as you type, debounced)
   - Style sidebar with presets and customization
   - Code editor for manual Mermaid/D2 tweaking
   - Export: SVG, PNG (2x, 3x), PDF, raw Mermaid/D2 code
2. FastAPI backend with generation queue
3. Diagram history and versioning

### Phase 4: Integrations (Week 4+)
1. VS Code extension: select text → generate diagram inline
2. Obsidian plugin: ```diagram code blocks
3. CLI tool: `diagramgpt "user authentication flow" --style professional --output auth-flow.svg`
4. API endpoint for embedding in other tools

### Key Design Decisions
- **Structured first**: always try Mermaid/D2 generation first (reliable, editable)
- **Fallback to SVG**: for diagram types Mermaid can't handle, generate raw SVG
- **Style consistency**: default output should look good without any customization
- **Editable output**: users can always edit the underlying code, not locked into AI output

### Environment Variables
```
LLM_PROVIDER=claude             # claude | openai | local
ANTHROPIC_API_KEY=your_key
MERMAID_CLI_PATH=mmdc
D2_PATH=d2
DEFAULT_STYLE=professional
OUTPUT_DIR=./diagrams/
```
