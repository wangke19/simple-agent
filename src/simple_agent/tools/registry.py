from __future__ import annotations

import logging

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: '{name}'")
        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def format_descriptions(self) -> str:
        return "\n".join(
            f"- {tool.name}: {tool.description}"
            for tool in self._tools.values()
        )
