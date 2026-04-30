"""Development workflow: plan → decompose → define contracts → execute → report."""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Any

from simple_agent.agent import SimpleAgent
from simple_agent.messages import Messages
from simple_agent.prompts import Prompts
from simple_agent.scaffold import ScaffoldConfig, ScaffoldResult, run_scaffold
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
        working_dir: str = ".",
        prompts: Prompts | None = None,
        messages: Messages | None = None,
        workflow_config: WorkflowConfig | None = None,
    ) -> None:
        self._agent = agent
        self._report_dir = report_dir
        self._working_dir = working_dir
        self._prompts = prompts or Prompts()
        self._msgs = messages or Messages()
        self._config = workflow_config or WorkflowConfig()
        self._plan: str = ""
        self._tasks: list[TaskItem] = []
        self._contract: str = ""
        self._task_results: list[dict[str, Any]] = []
        self._overall_report = TaskReport(task="")
        self._schema_block: str = ""
        self._scaffold_result: ScaffoldResult | None = None

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

    def scaffold(self, prd_path: str, output_dir: str, skip: bool = False) -> ScaffoldResult:
        """Phase 0: Create project skeleton and AGENT.md."""
        from pathlib import Path

        if skip:
            logger.info("=== Phase 0: Scaffold (skipped) ===")
            agent_md = Path(output_dir) / "AGENT.md"
            if agent_md.exists():
                self._scaffold_result = ScaffoldResult(
                    output_dir=output_dir,
                    agent_md_path=str(agent_md),
                    detected_frameworks=[],
                    rules_count=0,
                )
            return self._scaffold_result or ScaffoldResult(output_dir, "", [], 0)

        logger.info("=== Phase 0: Scaffold ===")
        config = ScaffoldConfig(prd_path=prd_path, output_dir=output_dir)
        self._scaffold_result = run_scaffold(config)
        logger.info(
            "Scaffold complete: frameworks=%s, rules=%d",
            self._scaffold_result.detected_frameworks,
            self._scaffold_result.rules_count,
        )
        return self._scaffold_result

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

        rules_block = self._build_rules_block()

        for i, task_item in enumerate(self._tasks):
            logger.info("--- Task %d/%d: %s ---", i + 1, len(self._tasks), task_item.description[:60])

            self._agent.reset()

            # Refresh schema before each task (earlier tasks may have created SQL files)
            self._refresh_schema_block()
            augmented_task = f"{task_item.description}{rules_block}{self._schema_block}{contract_block}"
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

            # Validate: import check on written files
            if status not in ("paused",) and self._agent.report:
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir)
                if validation_errors:
                    for err in validation_errors:
                        logger.warning("Validation error: %s", err)
                    status = "failed"
                    task_item.status = "failed"
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

        rules_block = self._build_rules_block()

        # Refresh schema for resume context
        self._refresh_schema_block()

        last_completed = len(self._task_results)
        for i in range(last_completed, len(self._tasks)):
            task_item = self._tasks[i]
            self._agent.reset()

            augmented_task = f"{task_item.description}{rules_block}{self._schema_block}{contract_block}"
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

        # Refresh schema for retry context
        self._refresh_schema_block()

        rules_block = self._build_rules_block()

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

            augmented_task = f"{read_preamble}{task_item.description}{rules_block}{self._schema_block}{contract_block}{context}"
            task_report = self._agent.run(augmented_task, max_steps=steps)
            status = self._agent.report.status if self._agent.report else "unknown"
            task_failures = self._agent.report.failed_steps if self._agent.report else 0

            if status == "failed":
                pass
            elif task_failures > 0 and status != "paused":
                status = "failed"

            task_item.retry_count += 1
            task_item.status = status

            # Validate: import check on written files
            if status not in ("paused",) and self._agent.report:
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir)
                if validation_errors:
                    for err in validation_errors:
                        logger.warning("Validation error: %s", err)
                    status = "failed"
                    task_item.status = "failed"

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
        """Scan the working directory for actual .py files."""
        from pathlib import Path
        base = Path(self._working_dir)
        if not base.exists():
            return []
        files = []
        for p in sorted(base.rglob("*.py")):
            rel = p.relative_to(base)
            # Skip hidden dirs, __pycache__, site-packages, .reports
            parts = rel.parts
            if any(part.startswith(".") or part == "__pycache__" or part == "site-packages" for part in parts):
                continue
            files.append(str(rel))
        return files

    def _refresh_schema_block(self) -> str:
        """Scan working dir for SQL schema files and build the injection block."""
        from pathlib import Path
        base = Path(self._working_dir)
        if not base.exists():
            return ""

        sql_files = sorted(base.glob("*.sql"))
        if not sql_files:
            return ""

        parts = []
        for sf in sql_files:
            try:
                content = sf.read_text(encoding="utf-8").strip()
                if content and any(kw in content.upper() for kw in ("CREATE TABLE", "CREATE VIEW")):
                    parts.append(f"### {sf.name}\n```sql\n{content}\n```")
            except Exception:
                continue

        if not parts:
            return ""

        schema_text = "\n\n".join(parts)
        self._schema_block = self._prompts.schema_injection_template.format(schema=schema_text)
        return self._schema_block

    def _build_rules_block(self) -> str:
        """Build the rules injection block from project AGENT.md and engineering standards."""
        from pathlib import Path
        from simple_agent.scaffold import _load_engineering_standards

        if not self._scaffold_result:
            return ""

        agent_md_path = Path(self._scaffold_result.agent_md_path)
        if not agent_md_path.exists():
            return ""

        project_rules = agent_md_path.read_text(encoding="utf-8")
        if not project_rules.strip():
            return ""

        engineering = _load_engineering_standards()

        return self._prompts.rules_injection_template.format(
            rules=project_rules,
            engineering_standards=engineering,
        )

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
    def _scan_all_py_files(working_dir: str) -> list[str]:
        """Recursively find all .py files in working_dir."""
        import pathlib
        base = pathlib.Path(working_dir)
        return sorted(str(p) for p in base.rglob("*.py"))

    @staticmethod
    def _validate_task_output(report: TaskReport, working_dir: str) -> list[str]:
        """Run import checks and SQL schema validation. Returns error messages."""
        import subprocess
        errors = []

        # Phase 1: Python import checks on all project files
        files = DevWorkflow._scan_all_py_files(working_dir)
        for filepath in files:
            check_code = (
                "import importlib.util, sys; "
                f"spec = importlib.util.spec_from_file_location('_check', '{filepath}'); "
                "mod = importlib.util.module_from_spec(spec); "
                "spec.loader.exec_module(mod)"
            )
            try:
                result = subprocess.run(
                    [sys.executable, "-c", check_code],
                    capture_output=True, text=True, timeout=10,
                    cwd=working_dir,
                )
                if result.returncode != 0:
                    errors.append(f"{filepath}: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                errors.append(f"{filepath}: import check timed out")

        # Phase 2: SQL column name validation against schema
        sql_errors = DevWorkflow._validate_sql_columns(working_dir)
        errors.extend(sql_errors)

        return errors

    @staticmethod
    def _validate_sql_columns(working_dir: str) -> list[str]:
        """Validate SQL queries in Python files against actual schema column names."""
        from pathlib import Path
        import re as _re

        base = Path(working_dir)
        if not base.exists():
            return []

        # Find and parse SQL schema files
        schema_tables: dict[str, set[str]] = {}
        for sf in sorted(base.glob("*.sql")):
            try:
                content = sf.read_text(encoding="utf-8")
            except Exception:
                continue
            for m in _re.finditer(
                r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)\s*;',
                content, _re.IGNORECASE | _re.DOTALL,
            ):
                table_name = m.group(1).lower()
                body = m.group(2)
                columns = set()
                for line in body.split("\n"):
                    line = line.strip().rstrip(",")
                    cm = _re.match(r'^(\w+)\s+', line)
                    if cm and cm.group(1).upper() not in (
                        'PRIMARY', 'UNIQUE', 'CHECK', 'FOREIGN', 'CONSTRAINT',
                        'INDEX', 'KEY', 'CREATE',
                    ):
                        columns.add(cm.group(1).lower())
                if columns:
                    schema_tables[table_name] = columns

        if not schema_tables:
            return []

        # Scan Python files for SQL queries and validate column references
        errors = []
        table_col_pattern = _re.compile(r'(\w+)\.(\w+)')

        for py_file in sorted(base.glob("*.py")):
            parts = py_file.relative_to(base).parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            sql_blocks = _re.findall(r'"""(.*?)"""', content, _re.DOTALL)
            sql_blocks += _re.findall(r"'''(.*?)'''", content, _re.DOTALL)

            for sql in sql_blocks:
                if not any(kw in sql.upper() for kw in ('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
                    continue

                alias_map: dict[str, str] = {}
                for tm in _re.finditer(
                    r'(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?',
                    sql, _re.IGNORECASE,
                ):
                    table = tm.group(1).lower()
                    alias = (tm.group(2) or tm.group(1)).lower()
                    if table in schema_tables:
                        alias_map[alias] = table

                if not alias_map:
                    continue

                for cm in table_col_pattern.finditer(sql):
                    alias = cm.group(1).lower()
                    col = cm.group(2).lower()
                    if alias in alias_map:
                        real_table = alias_map[alias]
                        valid_cols = schema_tables.get(real_table, set())
                        if valid_cols and col not in valid_cols:
                            rel = py_file.relative_to(base)
                            errors.append(
                                f"{rel}: column '{alias}.{col}' not in schema "
                                f"(table '{real_table}' has: {sorted(valid_cols)})"
                            )

        return errors

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
