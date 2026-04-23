from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    base_url: str
    api_key: str
    model: str
    max_steps: int = 5
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> AgentConfig:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
        if not api_key:
            raise AgentConfigError("ANTHROPIC_AUTH_TOKEN is not set")
        return cls(
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            api_key=api_key,
            model=os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-20250514"),
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "5")),
            log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
        )


class AgentConfigError(Exception):
    """Error in agent configuration."""
