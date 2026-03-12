# DiagramGPT

## Concept
An AI tool that generates publication-ready diagrams, architecture drawings, flowcharts, and technical illustrations from natural language descriptions. Outputs clean SVG/PNG with consistent styling — no more fighting with draw.io or spending 2 hours in Figma for a system architecture diagram.

Inspired by:
- **PaperBanana** (HF trending, Google, 214 upvotes) — automating academic illustration with vision-language models
- **Impeccable** (GitHub trending, 640 stars/day) — design language for AI interfaces
- **AFFiNE** (GitHub trending, 65k stars) — next-gen knowledge base with drawing capabilities

## Why It's Interesting
Technical diagrams are universally needed but universally hated to create. Existing tools (draw.io, Lucidchart, Mermaid) require manual layout or are limited to specific diagram types. PaperBanana proved that AI can generate publication-quality illustrations. This brings that capability to everyone — not just academic papers.

## Target Audience
- Developers writing documentation and architecture docs
- Technical writers and bloggers
- Researchers and academics
- Startup founders making pitch decks
- Students creating presentations

## Tech Stack
- **Core**: Python backend (FastAPI)
- **Diagram Generation**: Two-track approach:
  1. **Structured**: text → Mermaid/D2/PlantUML code → render (reliable, fast)
  2. **Visual**: text → SVG generation via LLM (flexible, creative)
- **Rendering**: mermaid-cli, D2, or custom SVG generation
- **Styling**: consistent design tokens (colors, fonts, spacing)
- **Frontend**: Next.js with live preview, style editor
- **Export**: SVG, PNG, PDF, Mermaid source

## Monetization
- **Freemium**: 10 diagrams/day, standard styles
- **Pro**: $12/mo — unlimited, custom styles, brand colors, team library
- **API**: $0.02/diagram for embedding in other tools
- **Integrations**: VS Code extension, Obsidian plugin, Notion embed
- **Templates**: premium diagram template packs by industry

## Key Differentiator
Two-track generation: structured (Mermaid/D2 for reliability) and visual (SVG for creativity). Most tools do one or the other. Plus: consistent, beautiful styling out of the box — not the default ugly boxes-and-arrows look.
