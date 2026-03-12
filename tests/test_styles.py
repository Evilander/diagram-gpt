"""Tests for style system."""

from src.styles.themes import d2_style_block, mermaid_theme_config
from src.styles.tokens import get_font, get_palette


def test_all_palettes_exist():
    for name in ["professional", "dark", "vibrant", "monochrome", "network"]:
        p = get_palette(name)
        assert p.name == name
        assert len(p.node_fills) >= 4


def test_unknown_palette_falls_back():
    p = get_palette("nonexistent")
    assert p.name == "professional"


def test_all_fonts_exist():
    for name in ["clean", "technical", "academic", "system"]:
        f = get_font(name)
        assert f.name == name


def test_mermaid_theme_config():
    config = mermaid_theme_config("professional", "clean")
    assert config["theme"] == "base"
    assert "primaryColor" in config["themeVariables"]
    assert "fontFamily" in config["themeVariables"]


def test_d2_style_block():
    style = d2_style_block("dark")
    assert "fill:" in style
    assert "stroke:" in style
