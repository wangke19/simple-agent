from __future__ import annotations

import logging

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

    def call(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        logger.debug("Sending request to model: %s", self._model)
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )
        except anthropic.APIConnectionError as e:
            raise LLMError(f"Connection error: {e}") from e
        except anthropic.RateLimitError as e:
            raise LLMError(f"Rate limit exceeded: {e}") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"API error (status {e.status_code}): {e}") from e

        text = response.content[0].text
        logger.debug("Response received: %d chars", len(text))
        return text
