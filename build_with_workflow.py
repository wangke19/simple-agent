"""Build an app using DevWorkflow: plan → decompose → contracts → execute → report.

Usage:
    python build_with_workflow.py my_task.md              # full run
    python build_with_workflow.py my_task.md --retry      # retry failed tasks only
"""
import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from simple_agent import SimpleAgent, DevWorkflow
from simple_agent.tools import (
    BashTool, EditTool, GrepTool, ReadTool, WriteTool,
)

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Build an app using DevWorkflow")
    parser.add_argument("requirement", nargs="?", default="requirement.txt",
                        help="Requirement file (default: requirement.txt)")
    parser.add_argument("--retry", action="store_true",
                        help="Retry only failed tasks from the latest report")
    parser.add_argument("--max-steps", type=int, default=8,
                        help="Max steps per task (default: 8)")
    args = parser.parse_args()

    logging.basicConfig(level="INFO")

    req_path = Path(__file__).parent / args.requirement
    if not req_path.exists():
        print(f"Error: requirement file not found: {req_path}")
        sys.exit(1)

    requirement = req_path.read_text(encoding="utf-8").strip()
    if not requirement:
        print(f"Error: {args.requirement} is empty")
        sys.exit(1)

    stem = req_path.stem
    output_dir = f"demo/{stem}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    agent = SimpleAgent(max_failures=3)
    agent._system_prompt = (
        "You are a Python development expert. Use tools to create and modify files, run commands.\n"
        "file_write params: path (filename), content (full code).\n"
        "Complete one task at a time, then give a brief summary."
    )

    agent.register_tool(WriteTool(working_dir=output_dir))
    agent.register_tool(ReadTool(working_dir=output_dir))
    agent.register_tool(EditTool(working_dir=output_dir))
    agent.register_tool(GrepTool(working_dir=output_dir))
    agent.register_tool(BashTool(working_dir=output_dir, timeout=30))

    wf = DevWorkflow(agent, report_dir=f"{output_dir}/.reports")

    if args.retry:
        # Retry mode: re-plan, skip completed tasks
        print("=" * 60)
        print(f"Retrying failed tasks for: {stem}")
        print("=" * 60)

        wf.plan_task(requirement)
        wf.decompose(requirement)
        wf.define_contracts(requirement)
        # Mark all tasks as "completed" initially, then retry_failed will re-run the failed ones
        wf._task_results = [{"index": i + 1, "task": t, "status": "completed", "result": "", "steps": 0, "failures": 0}
                           for i, t in enumerate(wf._tasks)]

        # Read the latest report to find failed tasks
        report_dir = Path(output_dir) / ".reports"
        reports = sorted(report_dir.glob("report_*.md"))
        if not reports:
            print("No previous reports found. Run without --retry first.")
            sys.exit(1)

        latest = reports[-1].read_text(encoding="utf-8")
        # Parse failed task numbers from checklist "- [ ] Task N: ..."
        import re
        failed_nums = [int(m) for m in re.findall(r"- \[ \] Task (\d+):", latest)]
        if not failed_nums:
            print("No failed tasks found in the latest report.")
            sys.exit(0)

        print(f"Failed tasks to retry: {failed_nums}")
        # Reset those tasks to failed status
        for num in failed_nums:
            idx = num - 1
            if idx < len(wf._task_results):
                wf._task_results[idx]["status"] = "failed"

        result = wf.retry_failed(max_steps_per_task=args.max_steps)
        print()
        print(result)
    else:
        # Full run
        print(f"Requirement loaded from: {args.requirement}")
        print(f"Output directory: {output_dir}")
        print(f"{'=' * 60}")
        print(requirement[:200])
        if len(requirement) > 200:
            print(f"... ({len(requirement)} chars total)")
        print()

        print("=" * 60)
        print("Phase 1: Planning")
        print("=" * 60)
        plan = wf.plan_task(requirement)
        print(plan)
        print()

        print("=" * 60)
        print("Phase 2: Decomposing")
        print("=" * 60)
        tasks = wf.decompose(requirement)
        for i, t in enumerate(tasks):
            print(f"  [{i+1}] {t}")
        print()

        print("=" * 60)
        print("Phase 2.5: Defining API Contracts")
        print("=" * 60)
        contract = wf.define_contracts(requirement)
        print(contract)
        print()

        print("=" * 60)
        print("Phase 3: Executing")
        print("=" * 60)
        result = wf.execute(max_steps_per_task=args.max_steps)
        print()
        print(result)

    # Final summary
    print()
    if wf.report:
        print(f"Report status: {wf.report.status}")
        print(f"Total steps: {wf.report.total_steps}, Failures: {wf.report.failed_steps}")

    if wf.report.status == "paused":
        print("\n>>> Agent paused. To resume:")
        print(">>> wf.resume('your guidance here')")


if __name__ == "__main__":
    main()
