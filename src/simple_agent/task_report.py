"""Task report: human-readable execution log and checklist."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class StepStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepRecord:
    step: int
    action: str           # "tool_call" or "answer"
    tool_name: str = ""
    tool_input: dict | None = None
    result: str = ""
    status: StepStatus = StepStatus.SUCCESS
    error: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat(timespec="seconds")


@dataclass
class TaskReport:
    task: str
    plan: str = ""
    steps: list[StepRecord] = field(default_factory=list)
    final_result: str = ""
    status: str = "running"  # running / paused / completed / failed
    pause_reason: str = ""
    created_at: str = ""
    finished_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.FAILED)

    @property
    def tool_calls(self) -> int:
        return sum(1 for s in self.steps if s.action == "tool_call")

    def add_step(self, **kwargs) -> StepRecord:
        record = StepRecord(step=len(self.steps) + 1, **kwargs)
        self.steps.append(record)
        return record

    def to_markdown(self) -> str:
        lines = [
            f"# Task Report",
            f"",
            f"- **Task**: {self.task}",
            f"- **Status**: {self.status}",
            f"- **Time**: {self.created_at} → {self.finished_at or '...'}",
            f"- **Steps**: {self.total_steps} total, {self.tool_calls} tool calls, {self.failed_steps} failed",
        ]
        if self.pause_reason:
            lines.append(f"- **Pause Reason**: {self.pause_reason}")
        lines.append("")

        if self.plan:
            lines.append("## Plan")
            lines.append(self.plan)
            lines.append("")

        lines.append("## Execution Log")
        lines.append("")
        lines.append("| # | Action | Detail | Status |")
        lines.append("|---|--------|--------|--------|")
        for s in self.steps:
            if s.action == "tool_call":
                detail = f"`{s.tool_name}`({self._truncate(json.dumps(s.tool_input, ensure_ascii=False), 60)})"
            else:
                detail = self._truncate(s.result, 80)
            lines.append(f"| {s.step} | {s.action} | {detail} | {s.status.value} |")
        lines.append("")

        if self.status in ("completed", "paused", "failed"):
            lines.append("## Checklist")
            lines.append("")
            tool_names = sorted({s.tool_name for s in self.steps if s.tool_name})
            for name in tool_names:
                ok = all(s.status == StepStatus.SUCCESS for s in self.steps if s.tool_name == name)
                mark = "x" if ok else " "
                lines.append(f"- [{mark}] Tool `{name}`")
            lines.append("")

        if self.final_result:
            lines.append("## Final Result")
            lines.append(self.final_result)
            lines.append("")

        if self.status == "paused":
            lines.append("## Human Guidance Needed")
            lines.append("Please review the report above and provide guidance.")
            lines.append("To resume: call `agent.resume(guidance='...')`")
            lines.append("")

        return "\n".join(lines)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(self.to_markdown(), encoding="utf-8")

    @staticmethod
    def _truncate(s: str, max_len: int) -> str:
        if len(s) <= max_len:
            return s
        return s[:max_len - 3] + "..."
