from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8500",
    "http://localhost:8500",
]


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "auto"  # auto | claude | openai
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-4-20250514"
    default_style: str = "professional"
    default_font: str = "clean"
    mermaid_cli_path: str = "mmdc"
    d2_path: str = "d2"
    output_dir: Path = Path("./diagrams")
    host: str = "127.0.0.1"
    port: int = 8500
    allowed_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_ALLOWED_ORIGINS))
    max_description_length: int = 4000
    max_data_context_length: int = 12000
    min_diagram_width: int = 640
    max_diagram_width: int = 2400
    min_diagram_height: int = 360
    max_diagram_height: int = 1800
    max_upload_bytes: int = 5_000_000
    llm_timeout_seconds: int = 60
    render_timeout_seconds: int = 45
    auto_save: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("llm_provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def normalized_allowed_origins(self) -> list[str]:
        if "*" in self.allowed_origins:
            return ["*"]
        return [origin.rstrip("/") for origin in self.allowed_origins]


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
