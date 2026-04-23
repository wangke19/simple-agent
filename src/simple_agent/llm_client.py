from __future__ import annotations

import logging
from typing import Any

import anthropic

from simple_agent.config import AgentConfig
from simple_agent.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: AgentConfig) -> None:
        self._client = anthropic.Anthropic(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self._model = config.model

    def call(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> anthropic.Message:
        logger.debug("Sending request to model: %s", self._model)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = self._client.messages.create(**kwargs)
        except anthropic.APIConnectionError as e:
            raise LLMError(f"Connection error: {e}") from e
        except anthropic.RateLimitError as e:
            raise LLMError(f"Rate limit exceeded: {e}") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"API error (status {e.status_code}): {e}") from e

        logger.debug("Response received, %d content blocks", len(response.content))
        return response
