from __future__ import annotations

import json
import logging

from simple_agent.config import AgentConfig
from simple_agent.exceptions import ResponseParseError, ToolError
from simple_agent.llm_client import LLMClient
from simple_agent.prompts import build_system_prompt
from simple_agent.tools.base import BaseTool
from simple_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class SimpleAgent:
    def __init__(
        self,
        config: AgentConfig | None = None,
        llm_client: LLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self._config = config or AgentConfig.from_env()
        self._llm = llm_client or LLMClient(self._config)
        self._tools = tool_registry or ToolRegistry()
        self._messages: list[dict[str, str]] = []

    def register_tool(self, tool: BaseTool) -> None:
        self._tools.register(tool)

    def run(self, task: str, max_steps: int | None = None) -> str:
        steps = max_steps or self._config.max_steps
        self._messages = [{"role": "user", "content": task}]
        system_prompt = build_system_prompt(self._tools.format_descriptions())

        for step in range(steps):
            logger.info("Step %d/%d", step + 1, steps)

            try:
                raw = self._llm.call(system_prompt, self._messages)
                decision = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse LLM response: %s", raw[:200])
                self._messages.append({
                    "role": "assistant",
                    "content": f"JSON解析错误，请重新回复。原始错误：{e}",
                })
                continue
            except ResponseParseError:
                raise

            if decision.get("type") == "answer":
                return decision["content"]

            if decision.get("type") == "tool":
                result = self._execute_tool(decision["tool"], decision["input"])
                self._messages.append({
                    "role": "assistant",
                    "content": f"工具 {decision['tool']} 返回：{result}",
                })
            else:
                logger.warning("Unknown decision type: %s", decision.get("type"))
                self._messages.append({
                    "role": "assistant",
                    "content": "未知的决策类型，请使用正确的JSON格式回复。",
                })

        return "超过最大步数"

    def _execute_tool(self, name: str, tool_input: str) -> str:
        try:
            tool = self._tools.get(name)
            return tool.execute(tool_input)
        except ToolError as e:
            logger.warning("Tool error: %s", e)
            return f"工具错误：{e}"
