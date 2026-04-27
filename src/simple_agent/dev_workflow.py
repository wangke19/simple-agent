"""Development workflow: plan → decompose → define contracts → execute → report."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from simple_agent.agent import SimpleAgent
from simple_agent.messages import Messages
from simple_agent.prompts import Prompts
from simple_agent.task_report import StepStatus, TaskReport

logger = logging.getLogger(__name__)


@dataclass
class TaskItem:
    """A single atomic task with dependency tracking and retry state."""
    index: int          # 1-based
    description: str
    depends_on: list[int] = field(default_factory=list)  # 0-based indices
    retry_count: int = 0
    status: str = "pending"  # pending / completed / failed / skipped


@dataclass
class WorkflowConfig:
    """Controls which workflow phases are enabled."""
    enable_plan: bool = True
    enable_decompose: bool = True
    enable_contracts: bool = True
    max_steps_per_task: int = 10


class DevWorkflow:
    """Orchestrates plan → decompose → define contracts → execute → report cycle."""

    def __init__(
        self,
        agent: SimpleAgent,
        report_dir: str = ".agent/reports",
        prompts: Prompts | None = None,
        messages: Messages | None = None,
        workflow_config: WorkflowConfig | None = None,
    ) -> None:
        self._agent = agent
        self._report_dir = report_dir
        self._prompts = prompts or Prompts()
        self._msgs = messages or Messages()
        self._config = workflow_config or WorkflowConfig()
        self._plan: str = ""
        self._tasks: list[TaskItem] = []
        self._contract: str = ""
        self._task_results: list[dict[str, Any]] = []
        self._overall_report = TaskReport(task="")

    @property
    def plan(self) -> str:
        return self._plan

    @property
    def tasks(self) -> list[TaskItem]:
        return self._tasks

    @property
    def contract(self) -> str:
        return self._contract

    @property
    def report(self) -> TaskReport:
        return self._overall_report

    @property
    def failed_task_indices(self) -> list[int]:
        """Return 0-based indices of failed tasks."""
        return [i for i, r in enumerate(self._task_results) if r["status"] not in ("completed", "skipped")]

    def run_all(self, requirement: str) -> str:
        """Execute all enabled phases in sequence."""
        if self._config.enable_plan:
            self.plan_task(requirement)
        if self._config.enable_decompose:
            self.decompose(requirement)
        if self._config.enable_contracts:
            self.define_contracts(requirement)
        return self.execute(max_steps_per_task=self._config.max_steps_per_task)

    def plan_task(self, requirement: str) -> str:
        """Phase 1: Generate a development plan."""
        logger.info("=== Phase 1: Planning ===")
        self._overall_report = TaskReport(task=requirement)

        original_prompt = self._agent._system_prompt
        original_tools = self._agent._tools

        self._agent._system_prompt = self._prompts.plan_prompt
        self._agent.reset()

        from simple_agent.tools.registry import ToolRegistry
        self._agent._tools = ToolRegistry()

        self._plan = self._agent.run(requirement, max_steps=1)

        self._agent._system_prompt = original_prompt
        self._agent._tools = original_tools
        self._agent.reset()

        self._overall_report.plan = self._plan
        self._tasks = self._parse_tasks(self._plan)
        logger.info("Plan generated: %d tasks", len(self._tasks))
        return self._plan

    def decompose(self, requirement: str) -> list[TaskItem]:
        """Phase 2: Decompose into atomic tasks."""
        logger.info("=== Phase 2: Decomposing ===")

        original_prompt = self._agent._system_prompt
        original_tools = self._agent._tools

        self._agent._system_prompt = self._prompts.decompose_prompt
        self._agent.reset()

        from simple_agent.tools.registry import ToolRegistry
        self._agent._tools = ToolRegistry()

        prompt = self._prompts.decompose_context_template.format(
            requirement=requirement, plan=self._plan,
        )
        result = self._agent.run(prompt, max_steps=1)

        self._agent._system_prompt = original_prompt
        self._agent._tools = original_tools
        self._agent.reset()

        self._tasks = self._parse_tasks(result)
        logger.info("Decomposed into %d atomic tasks", len(self._tasks))
        return self._tasks

    def define_contracts(self, requirement: str) -> str:
        """Phase 2.5: Define API contracts between modules."""
        logger.info("=== Phase 2.5: Defining API Contracts ===")

        original_prompt = self._agent._system_prompt
        original_tools = self._agent._tools

        self._agent._system_prompt = self._prompts.contract_prompt
        self._agent.reset()

        from simple_agent.tools.registry import ToolRegistry
        self._agent._tools = ToolRegistry()

        task_list = "\n".join(f"{i+1}. {t.description}" for i, t in enumerate(self._tasks))
        prompt = self._prompts.contract_context_template.format(
            requirement=requirement, plan=self._plan, task_list=task_list,
        )
        self._contract = self._agent.run(prompt, max_steps=1)

        self._agent._system_prompt = original_prompt
        self._agent._tools = original_tools
        self._agent.reset()

        logger.info("API contract defined (%d chars)", len(self._contract))
        return self._contract

    def execute(self, max_steps_per_task: int | None = None) -> str:
        """Phase 3: Execute each atomic task sequentially."""
        steps = max_steps_per_task or self._config.max_steps_per_task
        logger.info("=== Phase 3: Executing %d tasks ===", len(self._tasks))

        contract_block = ""
        if self._contract:
            contract_block = self._prompts.contract_injection_template.format(
                contract=self._contract,
            )

        for i, task_item in enumerate(self._tasks):
            logger.info("--- Task %d/%d: %s ---", i + 1, len(self._tasks), task_item.description[:60])

            self._agent.reset()

            augmented_task = f"{task_item.description}{contract_block}"
            task_report = self._agent.run(augmented_task, max_steps=steps)
            status = self._agent.report.status if self._agent.report else "unknown"
            task_failures = self._agent.report.failed_steps if self._agent.report else 0

            # Mark task as failed if it has significant failures or hit max steps
            if status == "failed":
                pass  # already failed
            elif task_failures > 0 and status != "paused":
                status = "failed"

            task_item.status = status
            if status == "failed":
                task_item.retry_count += 1

            self._task_results.append({
                "index": i + 1,
                "task": task_item.description,
                "status": status,
                "result": task_report,
                "steps": self._agent.report.total_steps if self._agent.report else 0,
                "failures": task_failures,
                "retry_count": task_item.retry_count,
            })

            if self._agent.report:
                for step in self._agent.report.steps:
                    self._overall_report.steps.append(step)

            logger.info("Task %d result: %s (status=%s)", i + 1, task_report[:60], status)

            if status == "paused":
                return self._pause_and_report(i)

        return self._finalize_report()

    def resume(self, guidance: str, max_steps: int | None = None) -> str:
        """Resume from a paused state with human guidance."""
        steps = max_steps or self._config.max_steps_per_task
        logger.info("=== Resuming with guidance ===")
        result = self._agent.resume(guidance, max_steps=steps)
        status = self._agent.report.status if self._agent.report else "unknown"

        if self._agent.report:
            for step in self._agent.report.steps:
                self._overall_report.steps.append(step)

        if status == "paused":
            paused_idx = len(self._task_results)
            return self._pause_and_report(paused_idx)

        contract_block = ""
        if self._contract:
            contract_block = self._prompts.contract_injection_template.format(
                contract=self._contract,
            )

        last_completed = len(self._task_results)
        for i in range(last_completed, len(self._tasks)):
            task_item = self._tasks[i]
            self._agent.reset()

            augmented_task = f"{task_item.description}{contract_block}"
            task_report = self._agent.run(augmented_task, max_steps=steps)
            status = self._agent.report.status if self._agent.report else "unknown"

            task_item.status = status

            self._task_results.append({
                "index": i + 1,
                "task": task_item.description,
                "status": status,
                "result": task_report,
                "retry_count": task_item.retry_count,
            })

            if self._agent.report:
                for step in self._agent.report.steps:
                    self._overall_report.steps.append(step)

            if status == "paused":
                return self._pause_and_report(i)

        return self._finalize_report()

    def retry_failed(self, max_steps_per_task: int | None = None) -> str:
        """Re-execute only the failed tasks, with file-reading preamble and retry boundary."""
        steps = max_steps_per_task or self._config.max_steps_per_task
        failed = self.failed_task_indices
        if not failed:
            logger.info("No failed tasks to retry")
            return self._finalize_report()

        logger.info("=== Retrying %d failed tasks ===", len(failed))

        contract_block = ""
        if self._contract:
            contract_block = self._prompts.contract_injection_template.format(
                contract=self._contract,
            )

        completed_tasks = [
            f"  {r['index']}. {r['task']}" for r in self._task_results
            if r["status"] == "completed"
        ]
        completed_files = self._extract_filenames()

        context_parts = []
        if completed_tasks:
            context_parts.append(
                "## Completed tasks (these are already done, do NOT redo them):\n"
                + "\n".join(completed_tasks)
            )
        if completed_files:
            context_parts.append(
                "## Existing files (read them FIRST with file_read before making changes):\n"
                + "\n".join(f"  - {f}" for f in completed_files)
            )

        context = ""
        if context_parts:
            context = "\n\n---\n" + "\n\n".join(context_parts) + "\n---"

        read_preamble = (
            "IMPORTANT: Before doing anything else, use file_read to read ALL existing files "
            "listed above. Understand the current code before making changes.\n\n"
        )

        for idx in failed:
            task_item = self._tasks[idx]

            if task_item.retry_count >= 3:
                has_dependents = any(
                    idx in self._tasks[j].depends_on
                    for j in range(len(self._tasks))
                    if j != idx and self._tasks[j].status in ("pending", "failed")
                )
                if has_dependents:
                    logger.warning("Task %d hit 3-retry limit with dependents — pausing", idx + 1)
                    task_item.status = "failed"
                    self._task_results[idx]["status"] = "failed"
                    return self._pause_and_report(idx)
                else:
                    logger.warning("Task %d hit 3-retry limit — skipping (no dependents)", idx + 1)
                    task_item.status = "skipped"
                    self._task_results[idx]["status"] = "skipped"
                    continue

            logger.info("--- Retry Task %d/%d: %s ---", idx + 1, len(self._tasks), task_item.description[:60])

            self._agent.reset()

            augmented_task = f"{read_preamble}{task_item.description}{contract_block}{context}"
            task_report = self._agent.run(augmented_task, max_steps=steps)
            status = self._agent.report.status if self._agent.report else "unknown"
            task_failures = self._agent.report.failed_steps if self._agent.report else 0

            if status == "failed":
                pass
            elif task_failures > 0 and status != "paused":
                status = "failed"

            task_item.retry_count += 1
            task_item.status = status

            self._task_results[idx] = {
                "index": idx + 1,
                "task": task_item.description,
                "status": status,
                "result": task_report,
                "steps": self._agent.report.total_steps if self._agent.report else 0,
                "failures": task_failures,
                "retry_count": task_item.retry_count,
            }

            if self._agent.report:
                for step in self._agent.report.steps:
                    self._overall_report.steps.append(step)

            logger.info("Retry Task %d result: %s (status=%s, retries=%d)", idx + 1, task_report[:60], status, task_item.retry_count)

            if status == "paused":
                return self._pause_and_report(idx)

        return self._finalize_report()

    def _extract_filenames(self) -> list[str]:
        """Extract filenames mentioned in the contract (### filename sections)."""
        filenames = set()
        if self._contract:
            for line in self._contract.split("\n"):
                m = re.match(r'^###\s+(\S+)', line)
                if m:
                    filenames.add(m.group(1))
        # Also scan task descriptions for common file patterns
        for t in self._tasks:
            for m in re.finditer(r'(\w+\.py(?:\w+)?)', t.description):
                filenames.add(m.group(1))
        return sorted(filenames)

    def _pause_and_report(self, task_index: int) -> str:
        msg = self._msgs.workflow_paused.format(
            current=task_index + 1,
            total=len(self._tasks),
            completed=task_index,
            remaining=len(self._tasks) - task_index,
        )
        self._overall_report.status = "paused"
        self._overall_report.pause_reason = f"Task {task_index + 1} paused"
        self._overall_report.final_result = msg
        self._save_report()
        return msg

    def _finalize_report(self) -> str:
        completed = sum(1 for r in self._task_results if r["status"] == "completed")
        skipped = sum(1 for r in self._task_results if r["status"] == "skipped")
        total = len(self._task_results)
        self._overall_report.status = "completed"
        self._overall_report.final_result = self._msgs.workflow_completed.format(
            total=total, passed=completed,
        )

        lines = [f"## Task Checklist ({completed}/{total} passed, {skipped} skipped)", ""]
        for r in self._task_results:
            if r["status"] == "completed":
                mark = "x"
            elif r["status"] == "skipped":
                mark = "~"
            else:
                mark = " "
            retry_info = f" (retries: {r.get('retry_count', 0)})" if r.get('retry_count', 0) > 0 else ""
            lines.append(f"- [{mark}] Task {r['index']}: {r['task'][:80]}{retry_info}")

        if self._contract:
            lines.append("")
            lines.append("## API Contract")
            lines.append(self._contract)

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
    def _parse_tasks(text: str) -> list[TaskItem]:
        """Parse numbered task list from LLM output, extracting dependency annotations."""
        tasks: list[TaskItem] = []
        for line in text.split("\n"):
            line = line.strip()
            m = re.match(r'^(?:\d+[\.\)]\s*|-\s*\[?\d+\]?\s*|\*\s*)(.+)', line)
            if not m or len(m.group(1).strip()) <= 5:
                continue
            raw = m.group(1).strip()
            # Extract [depends: 1, 3] or [depends: none]
            depends_on: list[int] = []
            dep_match = re.search(r'\[depends:\s*(.*?)\]', raw, re.IGNORECASE)
            has_annotation = dep_match is not None
            if dep_match:
                dep_text = dep_match.group(1).strip().lower()
                if dep_text != "none":
                    depends_on = [int(x.strip()) - 1 for x in dep_text.split(",") if x.strip().isdigit()]
                raw = re.sub(r'\s*\[depends:\s*.*?\]\s*', '', raw, flags=re.IGNORECASE).strip()
            task_item = TaskItem(
                index=len(tasks) + 1,
                description=raw,
                depends_on=depends_on,
            )
            tasks.append(task_item)
        # Fallback: if no annotation, depend on previous task
        for i, t in enumerate(tasks):
            if not t.depends_on and i > 0:
                t.depends_on = [i - 1]
        return tasks
