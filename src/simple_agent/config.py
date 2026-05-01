from __future__ import annotations

import json
import os
from dataclasses import dataclass

_CONFIG_FILE = "config/llm_config.json"


def _load_provider_presets() -> dict[str, dict[str, str]]:
    """Load provider presets from llm_config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", _CONFIG_FILE)
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


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
        provider = os.getenv("LLM_PROVIDER", "glm")
        presets = _load_provider_presets()
        preset = presets.get(provider, {})

        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or preset.get("api_key", "")
        if not api_key:
            raise AgentConfigError("ANTHROPIC_AUTH_TOKEN is not set")

        return cls(
            base_url=os.getenv("ANTHROPIC_BASE_URL") or preset.get("base_url", "https://api.anthropic.com"),
            api_key=api_key,
            model=os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL") or preset.get("model", "claude-sonnet-4-20250514"),
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "5")),
            log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
            max_context_tokens=int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "100000")),
            compact_threshold=float(os.getenv("AGENT_COMPACT_THRESHOLD", "0.8")),
            keep_recent_messages=int(os.getenv("AGENT_KEEP_RECENT_MESSAGES", "4")),
        )


class AgentConfigError(Exception):
    """Error in agent configuration."""
