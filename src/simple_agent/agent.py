from __future__ import annotations

import logging
from typing import Any

from simple_agent.config import AgentConfig
from simple_agent.compactor import compact_messages
from simple_agent.exceptions import ToolError
from simple_agent.llm_client import LLMClient
from simple_agent.task_report import StepStatus, TaskReport
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
        max_failures: int = 3,
    ) -> None:
        self._config = config or AgentConfig.from_env()
        self._llm = llm_client or LLMClient(self._config)
        self._tools = tool_registry or ToolRegistry()
        self._messages: list[dict[str, Any]] = []
        self._system_prompt: str | None = None
        self._max_failures = max_failures
        self._failure_count = 0
        self._report: TaskReport | None = None

    def register_tool(self, tool: BaseTool) -> None:
        self._tools.register(tool)

    def reset(self) -> None:
        """Clear conversation history."""
        self._messages = []

    @property
    def report(self) -> TaskReport | None:
        return self._report

    def run(self, task: str, max_steps: int | None = None) -> str:
        steps = max_steps or self._config.max_steps
        self._messages.append({"role": "user", "content": task})
        self._report = TaskReport(task=task)
        self._failure_count = 0

        system_prompt = self._system_prompt or "你是一个AI助手，可以使用工具来完成任务。请根据需要调用工具，或直接给出答案。"
        memory_tool = self._tools.get("memory") if "memory" in [t.name for t in self._tools.list_tools()] else None
        if memory_tool and isinstance(memory_tool, MemoryTool):
            memory_context = memory_tool.load_into_system_prompt()
            if memory_context:
                system_prompt += memory_context
        api_tools = self._tools.to_api_format()

        for step in range(steps):
            logger.info("Step %d/%d (failures: %d/%d)", step + 1, steps, self._failure_count, self._max_failures)

            self._messages = compact_messages(
                self._messages,
                keep_recent=self._config.keep_recent_messages,
                llm=self._llm,
                max_context_tokens=self._config.max_context_tokens,
                compact_threshold=self._config.compact_threshold,
            )

            try:
                response = self._llm.call(
                    system_prompt=system_prompt,
                    messages=self._messages,
                    tools=api_tools or None,
                )
            except Exception as e:
                self._failure_count += 1
                self._report.add_step(action="llm_call", status=StepStatus.FAILED, error=str(e))
                logger.error("LLM call failed (%d/%d): %s", self._failure_count, self._max_failures, e)
                if self._failure_count >= self._max_failures:
                    return self._pause("LLM调用连续失败", system_prompt)
                continue

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
                answer = "\n".join(text_parts)
                self._report.add_step(action="answer", result=answer, status=StepStatus.SUCCESS)
                self._report.status = "completed"
                self._report.final_result = answer
                self._failure_count = 0
                return answer

            assistant_content: list[dict[str, Any]] = []
            tool_result_content: list[dict[str, Any]] = []

            for block in response.content:
                assistant_content.append({"type": block.type, **_block_to_dict(block)})

            self._messages.append({"role": "assistant", "content": assistant_content})

            for tc in tool_calls:
                result, success = self._execute_tool(tc["name"], tc["input"])
                if not success:
                    self._failure_count += 1
                    self._report.add_step(
                        action="tool_call", tool_name=tc["name"],
                        tool_input=tc["input"], result=result,
                        status=StepStatus.FAILED, error=result,
                    )
                    if self._failure_count >= self._max_failures:
                        self._messages.append({"role": "user", "content": tool_result_content})
                        return self._pause(f"工具调用连续失败({self._failure_count}次)", system_prompt)
                else:
                    self._report.add_step(
                        action="tool_call", tool_name=tc["name"],
                        tool_input=tc["input"], result=result,
                        status=StepStatus.SUCCESS,
                    )
                    self._failure_count = 0  # reset on success

                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result,
                })

            self._messages.append({"role": "user", "content": tool_result_content})

        self._report.status = "failed"
        self._report.final_result = "超过最大步数"
        return "超过最大步数"

    def resume(self, guidance: str, max_steps: int | None = None) -> str:
        """Resume a paused task with human guidance."""
        if not self._report or self._report.status != "paused":
            raise RuntimeError("No paused task to resume")

        logger.info("Resuming with guidance: %s", guidance[:100])
        self._failure_count = 0
        self._report.status = "running"
        self._report.pause_reason = ""

        # Feed human guidance as a new user message
        self._messages.append({
            "role": "user",
            "content": f"人类指导：{guidance}\n\n请继续完成任务。",
        })
        self._report.add_step(action="human_guidance", result=guidance, status=StepStatus.SUCCESS)

        steps = max_steps or self._config.max_steps
        system_prompt = self._system_prompt or "你是一个AI助手，可以使用工具来完成任务。请根据需要调用工具，或直接给出答案。"
        api_tools = self._tools.to_api_format()

        for step in range(steps):
            logger.info("Resume step %d/%d", step + 1, steps)

            self._messages = compact_messages(
                self._messages,
                keep_recent=self._config.keep_recent_messages,
                llm=self._llm,
                max_context_tokens=self._config.max_context_tokens,
                compact_threshold=self._config.compact_threshold,
            )

            try:
                response = self._llm.call(
                    system_prompt=system_prompt,
                    messages=self._messages,
                    tools=api_tools or None,
                )
            except Exception as e:
                self._failure_count += 1
                self._report.add_step(action="llm_call", status=StepStatus.FAILED, error=str(e))
                if self._failure_count >= self._max_failures:
                    return self._pause("LLM调用连续失败(恢复后)", system_prompt)
                continue

            tool_calls: list[dict[str, Any]] = []
            text_parts: list[str] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append({"id": block.id, "name": block.name, "input": block.input})

            if not tool_calls:
                answer = "\n".join(text_parts)
                self._report.add_step(action="answer", result=answer, status=StepStatus.SUCCESS)
                self._report.status = "completed"
                self._report.final_result = answer
                self._failure_count = 0
                return answer

            assistant_content: list[dict[str, Any]] = []
            tool_result_content: list[dict[str, Any]] = []

            for block in response.content:
                assistant_content.append({"type": block.type, **_block_to_dict(block)})

            self._messages.append({"role": "assistant", "content": assistant_content})

            for tc in tool_calls:
                result, success = self._execute_tool(tc["name"], tc["input"])
                if not success:
                    self._failure_count += 1
                    self._report.add_step(
                        action="tool_call", tool_name=tc["name"],
                        tool_input=tc["input"], result=result,
                        status=StepStatus.FAILED, error=result,
                    )
                    if self._failure_count >= self._max_failures:
                        self._messages.append({"role": "user", "content": tool_result_content})
                        return self._pause("工具调用连续失败(恢复后)", system_prompt)
                else:
                    self._report.add_step(
                        action="tool_call", tool_name=tc["name"],
                        tool_input=tc["input"], result=result,
                        status=StepStatus.SUCCESS,
                    )
                    self._failure_count = 0

                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result,
                })

            self._messages.append({"role": "user", "content": tool_result_content})

        self._report.status = "failed"
        self._report.final_result = "超过最大步数(恢复后)"
        return "超过最大步数"

    def _pause(self, reason: str, system_prompt: str) -> str:
        """Pause execution and save report."""
        msg = f"任务暂停：{reason}。请查看报告并提供指导后重启。"
        self._report.status = "paused"
        self._report.pause_reason = reason
        self._report.final_result = msg
        logger.warning(msg)
        return msg

    def _execute_tool(self, name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        """Execute a tool. Returns (result, success)."""
        try:
            tool = self._tools.get(name)
            result = tool.execute(**tool_input)
            return result, True
        except (ToolError, Exception) as e:
            logger.warning("Tool error: %s", e)
            return f"工具错误：{e}", False


def _block_to_dict(block: Any) -> dict[str, Any]:
    if block.type == "text":
        return {"text": block.text}
    elif block.type == "tool_use":
        return {"id": block.id, "name": block.name, "input": block.input}
    return {}
