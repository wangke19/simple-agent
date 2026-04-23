from __future__ import annotations

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculate"
    description = "计算数学表达式"

    def execute(self, input: str) -> str:
        try:
            result = eval(input)  # noqa: S307
            return str(result)
        except Exception as e:
            raise ToolError(f"计算错误: {e}") from e
