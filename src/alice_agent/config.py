"""Configuration for Alice Agent using Pydantic Settings."""

from __future__ import annotations

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Yandex AI Studio Agent Atelier endpoint
AGENT_BASE_URL = "https://rest-assistant.api.cloud.yandex.net/v1"


class Settings(BaseSettings):
    """Alice Agent configuration loaded from environment variables.

    Only ONE API key is needed: ALICE_YC_API_KEY (Yandex Cloud IAM/API key).
    Web search is handled server-side by the Agent Atelier agent.
    """

    model_config = SettingsConfigDict(
        env_prefix="ALICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Yandex Cloud credentials
    yc_folder_id: str = "b1g6co0cfokq8k24mu7n"
    yc_api_key: SecretStr = SecretStr("")

    # Agent Atelier — the agent has WebSearch built in
    yc_prompt_id: str = "fvtvl13pf2lknmsk33to"

    # Agent behavior
    max_agent_steps: int = 15
    verbose: bool = False

    @field_validator("max_agent_steps")
    @classmethod
    def validate_max_steps(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError("max_agent_steps must be between 1 and 50")
        return v

    def is_configured(self) -> bool:
        """Check if the API key is set."""
        return bool(self.yc_api_key.get_secret_value())


# Singleton settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (for testing)."""
    global _settings
    _settings = None
