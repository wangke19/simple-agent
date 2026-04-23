from __future__ import annotations

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculate"
    description = "计算数学表达式"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "要计算的数学表达式"},
            },
            "required": ["input"],
        }

    def execute(self, **kwargs) -> str:
        expr = kwargs.get("input", "")
        try:
            result = eval(expr)  # noqa: S307
            return str(result)
        except Exception as e:
            raise ToolError(f"计算错误: {e}") from e
