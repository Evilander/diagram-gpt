"""LLM provider for diagram code generation."""

from ..config import settings
from .prompts import get_prompt
from .types import DiagramType, OutputFormat

SUPPORTED_LLM_PROVIDERS = {"auto", "openai", "claude"}


class ProviderConfigurationError(RuntimeError):
    """Raised when no working LLM provider is configured."""


def resolve_llm_provider() -> str:
    """Pick an active provider from config and available credentials."""
    provider = settings.llm_provider

    if provider not in SUPPORTED_LLM_PROVIDERS:
        raise ProviderConfigurationError(
            f"Unsupported LLM_PROVIDER '{provider}'. Choose one of: auto, openai, claude."
        )

    if provider == "auto":
        if settings.openai_api_key:
            return "openai"
        if settings.anthropic_api_key:
            return "claude"
        raise ProviderConfigurationError(
            "No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY before generating "
            "diagrams."
        )

    if provider == "openai" and not settings.openai_api_key:
        raise ProviderConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

    if provider == "claude" and not settings.anthropic_api_key:
        raise ProviderConfigurationError(
            "ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude."
        )

    return provider


def get_llm_status() -> dict:
    """Return safe provider diagnostics for status and doctor commands."""
    try:
        resolved_provider = resolve_llm_provider()
        ready = True
        error = None
    except ProviderConfigurationError as exc:
        resolved_provider = None
        ready = False
        error = str(exc)

    return {
        "configured_provider": settings.llm_provider,
        "resolved_provider": resolved_provider,
        "ready": ready,
        "error": error,
        "providers": {
            "openai": {
                "configured": bool(settings.openai_api_key),
                "model": settings.openai_model,
            },
            "claude": {
                "configured": bool(settings.anthropic_api_key),
                "model": settings.anthropic_model,
            },
        },
    }


async def generate_diagram_code(
    description: str,
    diagram_type: DiagramType,
    output_format: OutputFormat = OutputFormat.MERMAID,
    data_context: str = "",
) -> str:
    """Generate diagram source code from a natural language description."""
    system_prompt, user_prompt = get_prompt(
        description,
        diagram_type,
        output_format,
        data_context=data_context,
    )
    provider = resolve_llm_provider()

    if provider == "openai":
        return await _generate_openai(system_prompt, user_prompt)
    if provider == "claude":
        return await _generate_claude(system_prompt, user_prompt)

    raise ProviderConfigurationError(f"Unsupported LLM provider: {provider}")


def _strip_fences(raw: str) -> str:
    """Strip markdown code fences if present."""
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw


async def _generate_openai(system_prompt: str, user_prompt: str) -> str:
    """Generate using OpenAI API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
    )
    response = await client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = (response.choices[0].message.content or "").strip()
    if not raw:
        raise ProviderConfigurationError("OpenAI returned an empty completion.")
    return _strip_fences(raw)


async def _generate_claude(system_prompt: str, user_prompt: str) -> str:
    """Generate using Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=settings.llm_timeout_seconds,
    )
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = "\n".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()
    if not raw:
        raise ProviderConfigurationError("Claude returned an empty completion.")
    return _strip_fences(raw)


FIX_PROMPT = """The following {format} diagram code failed to render with this error:

ERROR: {error}

Original code:
```
{code}
```

Fix the code so it renders correctly. Common issues:
- "end" is a reserved keyword in Mermaid — rename it to "finish" or "done"
- Invalid node syntax — use `nodeId[Label]` not `nodeId(Type: Label)`
- Missing arrow syntax — use `-->` not `->`
- Unmatched brackets or parentheses

Output ONLY the fixed diagram code — no markdown fences, no explanations."""


async def fix_diagram_code(
    original_code: str,
    error_message: str,
    output_format: OutputFormat,
) -> str:
    """Ask the LLM to fix broken diagram code using the error message."""
    # Truncate long error messages to the useful part
    error_short = error_message[:500]
    prompt = FIX_PROMPT.format(
        format=output_format.value.upper(),
        error=error_short,
        code=original_code,
    )

    provider = resolve_llm_provider()

    if provider == "openai":
        return await _generate_openai("You fix diagram code. Output only fixed code.", prompt)
    if provider == "claude":
        return await _generate_claude("You fix diagram code. Output only fixed code.", prompt)

    return original_code
