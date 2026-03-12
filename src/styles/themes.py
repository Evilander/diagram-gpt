"""Generate Mermaid theme configs and D2 style strings from design tokens."""

from .tokens import get_font, get_palette


def mermaid_theme_config(palette_name: str = "professional", font_name: str = "clean") -> dict:
    """Generate a Mermaid themeVariables config dict."""
    p = get_palette(palette_name)
    f = get_font(font_name)
    return {
        "theme": "base",
        "themeVariables": {
            "primaryColor": p.node_fills[0],
            "primaryTextColor": p.text,
            "primaryBorderColor": p.primary,
            "secondaryColor": p.node_fills[1],
            "secondaryTextColor": p.text,
            "secondaryBorderColor": p.secondary,
            "tertiaryColor": p.node_fills[2],
            "tertiaryTextColor": p.text,
            "tertiaryBorderColor": p.accent,
            "lineColor": p.border,
            "textColor": p.text,
            "mainBkg": p.surface,
            "nodeBorder": p.primary,
            "clusterBkg": p.surface,
            "clusterBorder": p.border,
            "titleColor": p.text,
            "edgeLabelBackground": p.background,
            "fontFamily": f.body,
            "fontSize": "14px",
        },
    }


def d2_style_block(palette_name: str = "professional") -> str:
    """Generate a D2 style block string."""
    p = get_palette(palette_name)
    return f"""style: {{
  fill: "{p.surface}"
  stroke: "{p.primary}"
  stroke-width: 2
  font-color: "{p.text}"
  border-radius: 8
  shadow: true
}}
"""
