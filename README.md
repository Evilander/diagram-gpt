# DiagramGPT

DiagramGPT is a structured-first diagram generation project for turning natural language into clean technical diagrams.

The current repository is an initial public scaffold. The target product is:

- Text to Mermaid, D2, and SVG diagrams
- Publication-ready system architecture and flowchart output
- A style system with reusable themes and export presets
- A CLI, API, and web UI for iterative editing and rendering

## Why This Exists

Most diagram tools are either manual and slow or automated but visually weak. DiagramGPT is meant to close that gap by generating diagrams that are both editable and presentation-ready.

## Planned Capabilities

- Structured generation first, with Mermaid and D2 as editable intermediate formats
- Native SVG fallback for custom layouts and richer visual control
- Diagram styles for professional docs, slideware, and brand-aligned outputs
- Validation and retry loops for safer generation
- Export targets including SVG, PNG, PDF, and source code

## Repository Layout

```text
src/        backend and generation pipeline
templates/  prompt and diagram templates
tests/      automated coverage
web/        future frontend application
```

## Status

This repo is public and bootstrapped, but the core implementation is still being built.

## Near-Term Roadmap

1. Add a working prompt-to-diagram pipeline
2. Support Mermaid and D2 output generation
3. Add a local render path for SVG previews
4. Expose generation through a small API and CLI

## Vision

The goal is not just to generate diagrams. The goal is to generate diagrams that developers, researchers, and founders would actually keep and ship without spending another hour fixing layout by hand.
