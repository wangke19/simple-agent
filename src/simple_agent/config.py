from __future__ import annotations

import os
from dataclasses import dataclass, field

_PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/anthropic",
        "model": "glm-4.7",
    },
    "minimax": {
        "base_url": "https://api.minimaxi.com/anthropic",
        "model": "MiniMax-M2.7",
    },
}


@dataclass
class AgentConfig:
    base_url: str
    api_key: str
    model: str
    max_steps: int = 5
    log_level: str = "INFO"
    max_context_tokens: int = 100000
    compact_threshold: float = 0.8
    keep_recent_messages: int = 4

    @classmethod
    def from_env(cls) -> AgentConfig:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
        if not api_key:
            raise AgentConfigError("ANTHROPIC_AUTH_TOKEN is not set")

        provider = os.getenv("LLM_PROVIDER", "")
        preset = _PROVIDER_PRESETS.get(provider, {})

        return cls(
            base_url=os.getenv("ANTHROPIC_BASE_URL") or preset.get("base_url", "https://api.anthropic.com"),
            api_key=api_key,
            model=os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL") or preset.get("model", "claude-sonnet-4-20250514"),
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "5")),
            log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
            max_context_tokens=int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "100000")),
            compact_threshold=float(os.getenv("AGET_COMPACT_THRESHOLD", "0.8")),
            keep_recent_messages=int(os.getenv("AGENT_KEEP_RECENT_MESSAGES", "4")),
        )


class AgentConfigError(Exception):
    """Error in agent configuration."""
