"""Configurable status and error messages."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Messages:
    """All status/error messages with English defaults."""

    # Agent status
    llm_failures: str = "Consecutive LLM call failures"
    tool_failures: str = "Consecutive tool call failures ({count} times)"
    max_steps_exceeded: str = "Maximum steps exceeded"
    llm_failures_resumed: str = "Consecutive LLM call failures (after resume)"
    tool_failures_resumed: str = "Consecutive tool call failures (after resume)"
    max_steps_resumed: str = "Maximum steps exceeded (after resume)"
    task_paused: str = "Task paused: {reason}. Review the report and provide guidance to resume."
    tool_error: str = "Tool error: {error}"
    no_paused_task: str = "No paused task to resume"

    # Workflow
    workflow_paused: str = (
        "Task paused at step {current}/{total}. "
        "Completed {completed} tasks, {remaining} remaining. "
        "Review the report and call resume(guidance='...') to continue."
    )
    workflow_completed: str = "All {total} tasks completed, {passed} successful."


def chinese_messages() -> Messages:
    """Return Messages with Chinese defaults (backward compatibility)."""
    return Messages(
        llm_failures="LLM调用连续失败",
        tool_failures="工具调用连续失败({count}次)",
        max_steps_exceeded="超过最大步数",
        llm_failures_resumed="LLM调用连续失败(恢复后)",
        tool_failures_resumed="工具调用连续失败(恢复后)",
        max_steps_resumed="超过最大步数(恢复后)",
        task_paused="任务暂停：{reason}。请查看报告并提供指导后重启。",
        tool_error="工具错误：{error}",
        no_paused_task="没有暂停的任务可恢复",
        workflow_paused=(
            "任务在步骤 {current}/{total} 暂停。\n"
            "已完成 {completed} 个任务，剩余 {remaining} 个。\n"
            "请查看报告，分析问题后调用 resume(guidance='...') 继续。"
        ),
        workflow_completed="全部 {total} 个任务完成，{passed} 个成功。",
    )
