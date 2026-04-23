from __future__ import annotations

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculate"

    @property
    def _default_description(self) -> str:
        return "Evaluate a mathematical expression."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Mathematical expression to evaluate"},
            },
            "required": ["input"],
        }

    def execute(self, **kwargs) -> str:
        expr = kwargs.get("input", "")
        try:
            result = eval(expr)  # noqa: S307
            return str(result)
        except Exception as e:
            raise ToolError(f"Evaluation error: {e}") from e
