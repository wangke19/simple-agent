from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str  # class attribute

    def __init__(self, description: str | None = None) -> None:
        self._description_override = description

    @property
    def description(self) -> str:
        return self._description_override or self._default_description

    @property
    def _default_description(self) -> str:
        return ""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Tool input"},
            },
            "required": ["input"],
        }

    @abstractmethod
    def execute(self, **kwargs: Any) -> str: ...
