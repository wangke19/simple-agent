from __future__ import annotations

from simple_agent.tools.base import BaseTool


class SearchTool(BaseTool):
    name = "search"
    description = "搜索信息"

    def execute(self, input: str) -> str:
        return f"搜索'{input}'的结果：今天北京晴天，25度"
