"""Development workflow: plan → decompose → execute → report."""
from __future__ import annotations

import logging
from typing import Any

from simple_agent.agent import SimpleAgent
from simple_agent.task_report import StepStatus, TaskReport
from simple_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)

PLAN_PROMPT = """你是一个项目规划专家。请为以下任务创建开发计划。

输出格式要求（严格遵守）：
1. 先输出"## 需求分析"段落，简述要做什么
2. 然后输出"## 任务拆解"段落，列出原子任务，每个任务一行，格式为：
   - [任务编号] 任务描述
   每个任务应该是一个独立的、可验证的小步骤
3. 不要输出其他内容"""

DECOMPOSE_PROMPT = """根据以下计划，请把任务拆解为具体的原子任务列表。
每个任务必须是：
- 独立的：可以单独执行和验证
- 小的：一次文件写入或一次命令执行
- 有序的：有明确的先后依赖

输出格式（严格遵守），每行一个任务：
1. 创建 xxx 文件，包含 yyy 功能
2. 创建 zzz 文件，包含 www 功能
3. 运行测试验证

只输出编号列表，不要其他内容。"""


class DevWorkflow:
    """Orchestrates plan → decompose → execute → report cycle."""

    def __init__(
        self,
        agent: SimpleAgent,
        report_dir: str = ".agent/reports",
    ) -> None:
        self._agent = agent
        self._report_dir = report_dir
        self._plan: str = ""
        self._tasks: list[str] = []
        self._task_results: list[dict[str, Any]] = []
        self._overall_report = TaskReport(task="")

    @property
    def plan(self) -> str:
        return self._plan

    @property
    def tasks(self) -> list[str]:
        return self._tasks

    @property
    def report(self) -> TaskReport:
        return self._overall_report

    def plan_task(self, requirement: str) -> str:
        """Phase 1: Generate a development plan."""
        logger.info("=== Phase 1: Planning ===")
        self._overall_report = TaskReport(task=requirement)

        # Use agent to generate plan (no tools needed, just reasoning)
        original_prompt = self._agent._system_prompt
        original_tools = self._agent._tools

        self._agent._system_prompt = PLAN_PROMPT
        self._agent.reset()

        # Temporarily remove tools so LLM just reasons
        from simple_agent.tools.registry import ToolRegistry
        self._agent._tools = ToolRegistry()

        self._plan = self._agent.run(requirement, max_steps=1)

        # Restore
        self._agent._system_prompt = original_prompt
        self._agent._tools = original_tools
        self._agent.reset()

        self._overall_report.plan = self._plan
        self._tasks = self._parse_tasks(self._plan)
        logger.info("Plan generated: %d tasks", len(self._tasks))
        return self._plan

    def decompose(self, requirement: str) -> list[str]:
        """Phase 2: Decompose into atomic tasks."""
        logger.info("=== Phase 2: Decomposing ===")

        original_prompt = self._agent._system_prompt
        original_tools = self._agent._tools

        self._agent._system_prompt = DECOMPOSE_PROMPT
        self._agent.reset()

        from simple_agent.tools.registry import ToolRegistry
        self._agent._tools = ToolRegistry()

        prompt = f"原始需求：{requirement}\n\n初步计划：\n{self._plan}"
        result = self._agent.run(prompt, max_steps=1)

        self._agent._system_prompt = original_prompt
        self._agent._tools = original_tools
        self._agent.reset()

        self._tasks = self._parse_tasks(result)
        logger.info("Decomposed into %d atomic tasks", len(self._tasks))
        return self._tasks

    def execute(self, max_steps_per_task: int = 10) -> str:
        """Phase 3: Execute each atomic task sequentially."""
        logger.info("=== Phase 3: Executing %d tasks ===", len(self._tasks))

        results = []
        for i, task_desc in enumerate(self._tasks):
            logger.info("--- Task %d/%d: %s ---", i + 1, len(self._tasks), task_desc[:60])

            # Reset conversation for each task to keep context small
            self._agent.reset()

            task_report = self._agent.run(task_desc, max_steps=max_steps_per_task)
            status = self._agent.report.status if self._agent.report else "unknown"

            self._task_results.append({
                "index": i + 1,
                "task": task_desc,
                "status": status,
                "result": task_report,
                "steps": self._agent.report.total_steps if self._agent.report else 0,
                "failures": self._agent.report.failed_steps if self._agent.report else 0,
            })

            if self._agent.report:
                for step in self._agent.report.steps:
                    self._overall_report.steps.append(step)

            logger.info("Task %d result: %s (status=%s)", i + 1, task_report[:60], status)

            if status == "paused":
                return self._pause_and_report(i)

        return self._finalize_report()

    def resume(self, guidance: str, max_steps: int = 10) -> str:
        """Resume from a paused state with human guidance."""
        logger.info("=== Resuming with guidance ===")
        result = self._agent.resume(guidance, max_steps=max_steps)
        status = self._agent.report.status if self._agent.report else "unknown"

        if self._agent.report:
            for step in self._agent.report.steps:
                self._overall_report.steps.append(step)

        if status == "paused":
            # Find which task we were on
            paused_idx = len(self._task_results)
            return self._pause_and_report(paused_idx)

        # If completed, continue with remaining tasks
        last_completed = len(self._task_results)
        for i in range(last_completed, len(self._tasks)):
            task_desc = self._tasks[i]
            self._agent.reset()

            task_report = self._agent.run(task_desc, max_steps=max_steps)
            status = self._agent.report.status if self._agent.report else "unknown"

            self._task_results.append({
                "index": i + 1,
                "task": task_desc,
                "status": status,
                "result": task_report,
            })

            if self._agent.report:
                for step in self._agent.report.steps:
                    self._overall_report.steps.append(step)

            if status == "paused":
                return self._pause_and_report(i)

        return self._finalize_report()

    def _pause_and_report(self, task_index: int) -> str:
        msg = (
            f"任务在步骤 {task_index + 1}/{len(self._tasks)} 暂停。\n"
            f"已完成 {task_index} 个任务，剩余 {len(self._tasks) - task_index} 个。\n"
            f"请查看报告，分析问题后调用 resume(guidance='...') 继续。"
        )
        self._overall_report.status = "paused"
        self._overall_report.pause_reason = f"任务 {task_index + 1} 暂停"
        self._overall_report.final_result = msg
        self._save_report()
        return msg

    def _finalize_report(self) -> str:
        completed = sum(1 for r in self._task_results if r["status"] == "completed")
        total = len(self._task_results)
        self._overall_report.status = "completed"
        self._overall_report.final_result = f"全部 {total} 个任务完成，{completed} 个成功。"

        # Build checklist
        lines = [f"## Task Checklist ({completed}/{total} passed)", ""]
        for r in self._task_results:
            mark = "x" if r["status"] == "completed" else " "
            lines.append(f"- [{mark}] Task {r['index']}: {r['task'][:80]}")
        self._overall_report.final_result += "\n\n" + "\n".join(lines)

        self._save_report()
        return self._overall_report.final_result

    def _save_report(self) -> None:
        from pathlib import Path
        from datetime import datetime
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = Path(self._report_dir) / filename
        self._overall_report.save(path)
        logger.info("Report saved to %s", path)

    @staticmethod
    def _parse_tasks(text: str) -> list[str]:
        """Parse numbered task list from LLM output."""
        import re
        tasks = []
        for line in text.split("\n"):
            line = line.strip()
            # Match "1. xxx" or "- [1] xxx" or "* 1) xxx" patterns
            m = re.match(r'^(?:\d+[\.\)]\s*|-\s*\[?\d+\]?\s*|\*\s*)(.+)', line)
            if m and len(m.group(1).strip()) > 5:
                tasks.append(m.group(1).strip())
        return tasks
