"""Tests for prompt selection."""

from src.generators.prompts import get_prompt
from src.generators.types import DiagramType, OutputFormat


def test_d2_prompt_falls_back_to_generic_template():
    system_prompt, user_prompt = get_prompt(
        "customer onboarding flow",
        DiagramType.FLOWCHART,
        OutputFormat.D2,
    )

    assert "Output valid D2 syntax only." in user_prompt
    assert "Mermaid" not in user_prompt
    assert "DiagramGPT" in system_prompt

