from __future__ import annotations

import logging
from typing import Any

import anthropic

from simple_agent.config import AgentConfig
from simple_agent.compactor import compact_messages
from simple_agent.exceptions import ToolError
from simple_agent.llm_client import LLMClient
from simple_agent.tools.base import BaseTool
from simple_agent.tools.memory import MemoryTool
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
        self._messages: list[dict[str, Any]] = []
        self._system_prompt: str | None = None

    def register_tool(self, tool: BaseTool) -> None:
        self._tools.register(tool)

    def reset(self) -> None:
        """Clear conversation history."""
        self._messages = []

    def run(self, task: str, max_steps: int | None = None) -> str:
        steps = max_steps or self._config.max_steps
        self._messages.append({"role": "user", "content": task})
        system_prompt = self._system_prompt or "你是一个AI助手，可以使用工具来完成任务。请根据需要调用工具，或直接给出答案。"
        memory_tool = self._tools.get("memory") if "memory" in [t.name for t in self._tools.list_tools()] else None
        if memory_tool and isinstance(memory_tool, MemoryTool):
            memory_context = memory_tool.load_into_system_prompt()
            if memory_context:
                system_prompt += memory_context
        api_tools = self._tools.to_api_format()

        for step in range(steps):
            logger.info("Step %d/%d", step + 1, steps)

            self._messages = compact_messages(
                self._messages,
                keep_recent=self._config.keep_recent_messages,
                llm=self._llm,
                max_context_tokens=self._config.max_context_tokens,
                compact_threshold=self._config.compact_threshold,
            )

            response = self._llm.call(
                system_prompt=system_prompt,
                messages=self._messages,
                tools=api_tools or None,
            )

            # Process response content blocks
            tool_calls: list[dict[str, Any]] = []
            text_parts: list[str] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            if not tool_calls:
                # No tool calls — LLM is done, return text answer
                return "\n".join(text_parts)

            # Execute tool calls and build assistant message + tool results
            assistant_content: list[dict[str, Any]] = []
            tool_result_content: list[dict[str, Any]] = []

            for block in response.content:
                assistant_content.append({"type": block.type, **_block_to_dict(block)})

            self._messages.append({"role": "assistant", "content": assistant_content})

            for tc in tool_calls:
                result = self._execute_tool(tc["name"], tc["input"])
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result,
                })

            self._messages.append({"role": "user", "content": tool_result_content})

        return "超过最大步数"

    def _execute_tool(self, name: str, tool_input: dict[str, Any]) -> str:
        try:
            tool = self._tools.get(name)
            return tool.execute(**tool_input)
        except ToolError as e:
            logger.warning("Tool error: %s", e)
            return f"工具错误：{e}"


def _block_to_dict(block: Any) -> dict[str, Any]:
    """Convert an Anthropic content block to a dict for message history."""
    if block.type == "text":
        return {"text": block.text}
    elif block.type == "tool_use":
        return {"id": block.id, "name": block.name, "input": block.input}
    return {}
