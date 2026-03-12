"""Design tokens for consistent diagram styling."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    name: str
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_muted: str
    border: str
    success: str
    warning: str
    error: str
    node_fills: list[str]  # rotating fills for distinct nodes


PALETTES = {
    "professional": ColorPalette(
        name="professional",
        primary="#2563eb",
        secondary="#7c3aed",
        accent="#0891b2",
        background="#ffffff",
        surface="#f8fafc",
        text="#0f172a",
        text_muted="#64748b",
        border="#e2e8f0",
        success="#16a34a",
        warning="#d97706",
        error="#dc2626",
        node_fills=["#dbeafe", "#ede9fe", "#cffafe", "#fef3c7", "#dcfce7", "#fce7f3"],
    ),
    "dark": ColorPalette(
        name="dark",
        primary="#60a5fa",
        secondary="#a78bfa",
        accent="#22d3ee",
        background="#0f172a",
        surface="#1e293b",
        text="#f1f5f9",
        text_muted="#94a3b8",
        border="#334155",
        success="#4ade80",
        warning="#fbbf24",
        error="#f87171",
        node_fills=["#1e3a5f", "#2d1b69", "#164e63", "#78350f", "#14532d", "#831843"],
    ),
    "vibrant": ColorPalette(
        name="vibrant",
        primary="#8b5cf6",
        secondary="#ec4899",
        accent="#06b6d4",
        background="#fafafa",
        surface="#ffffff",
        text="#18181b",
        text_muted="#71717a",
        border="#e4e4e7",
        success="#22c55e",
        warning="#f59e0b",
        error="#ef4444",
        node_fills=["#c4b5fd", "#f9a8d4", "#67e8f9", "#fde68a", "#86efac", "#fca5a5"],
    ),
    "monochrome": ColorPalette(
        name="monochrome",
        primary="#404040",
        secondary="#737373",
        accent="#525252",
        background="#ffffff",
        surface="#fafafa",
        text="#171717",
        text_muted="#737373",
        border="#d4d4d4",
        success="#404040",
        warning="#525252",
        error="#262626",
        node_fills=["#e5e5e5", "#d4d4d4", "#f5f5f5", "#a3a3a3", "#ededed", "#c4c4c4"],
    ),
    "network": ColorPalette(
        name="network",
        primary="#0284c7",
        secondary="#0369a1",
        accent="#0ea5e9",
        background="#f0f9ff",
        surface="#ffffff",
        text="#0c4a6e",
        text_muted="#64748b",
        border="#bae6fd",
        success="#059669",
        warning="#d97706",
        error="#dc2626",
        node_fills=["#bae6fd", "#a7f3d0", "#fde68a", "#c7d2fe", "#fbcfe8", "#fed7aa"],
    ),
}


@dataclass(frozen=True)
class FontPreset:
    name: str
    heading: str
    body: str
    code: str


FONTS = {
    "clean": FontPreset("clean", "Inter", "Inter", "JetBrains Mono"),
    "technical": FontPreset("technical", "JetBrains Mono", "JetBrains Mono", "JetBrains Mono"),
    "academic": FontPreset("academic", "Computer Modern", "Computer Modern", "Computer Modern"),
    "system": FontPreset("system", "system-ui", "system-ui", "monospace"),
}


def get_palette(name: str) -> ColorPalette:
    return PALETTES.get(name, PALETTES["professional"])


def get_font(name: str) -> FontPreset:
    return FONTS.get(name, FONTS["clean"])
