from __future__ import annotations

from simple_agent.tools.base import BaseTool


class SearchTool(BaseTool):
    name = "search"

    @property
    def _default_description(self) -> str:
        return "Search for information (placeholder)."

    def execute(self, **kwargs) -> str:
        query = kwargs.get("input", "")
        return f"Search results for '{query}': (placeholder - no search backend configured)"
