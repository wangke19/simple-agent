"""Build an app using DevWorkflow: plan → decompose → contracts → execute → report.

Usage:
    python build_with_workflow.py my_task.md              # full run (auto-retries failures)
    python build_with_workflow.py my_task.md --retry      # retry failed tasks only
    python build_with_workflow.py my_task.md --fix        # auto-fix runtime errors
    python build_with_workflow.py my_task.md --show-report # show latest report
    python build_with_workflow.py --list-reports           # list all reports for all tasks
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


def _show_report(report_dir: Path) -> None:
    """Show the latest report."""
    reports = sorted(report_dir.glob("report_*.md"))
    if not reports:
        print(f"No reports found in {report_dir}")
        sys.exit(1)
    print(reports[-1].read_text(encoding="utf-8"))


def _list_all_reports() -> None:
    """List all reports across all demo dirs."""
    demo_dir = Path(__file__).parent / "demo"
    if not demo_dir.exists():
        print("No demo directory found.")
        return

    found = False
    for report_dir in sorted(demo_dir.glob("*/.reports")):
        reports = sorted(report_dir.glob("report_*.md"))
        if reports:
            task_name = report_dir.parent.name
            print(f"\n{task_name}/")
            for r in reports:
                # Extract status line from report
                content = r.read_text(encoding="utf-8")
                status_line = ""
                for line in content.split("\n"):
                    if "**Status**" in line:
                        status_line = line.strip()
                        break
                print(f"  {r.name}  {status_line}")
            found = True

    if not found:
        print("No reports found.")
    else:
        print(f"\nUse --show-report with a requirement file to view details:")
        print(f"  python build_with_workflow.py student_mgmt.md --show-report")


def _run_retry(wf: DevWorkflow, max_steps: int) -> None:
    """Run one retry round for failed tasks."""
    result = wf.retry_failed(max_steps_per_task=max_steps)
    print()
    print(result)


def _parse_traceback(stderr: str) -> list[dict]:
    """Parse Python tracebacks into structured errors. Returns [{file, line, error}]."""
    import re
    errors = []
    lines = stderr.strip().split("\n")
    error_msg = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("File ") and not stripped.startswith("During"):
            error_msg = stripped
            break

    pattern = r'File "(.+?\.py)", line (\d+)'
    for match in re.finditer(pattern, stderr):
        filepath = match.group(1)
        lineno = match.group(2)
        if "/site-packages/" not in filepath:
            errors.append({"file": filepath, "line": int(lineno), "error": error_msg})
    return errors


def _smoke_test(output_dir: str) -> list[str]:
    """Run the generated app and capture errors. Returns list of error strings."""
    import subprocess
    import os
    output_path = Path(output_dir).resolve()

    main_py = output_path / "main.py"
    app_py = output_path / "app.py"
    entry_point = main_py if main_py.exists() else app_py if app_py.exists() else None
    if not entry_point:
        return []

    try:
        env = {"QT_QPA_PLATFORM": "offscreen", "PATH": os.environ.get("PATH", "")}
        result = subprocess.run(
            [sys.executable, str(entry_point)],
            capture_output=True, text=True, timeout=15,
            cwd=str(output_path), env=env,
        )
        if result.returncode != 0 and result.stderr:
            return [line for line in result.stderr.strip().split("\n") if line.strip()]
        return []
    except subprocess.TimeoutExpired:
        return []  # timeout = app ran (GUI event loop), not an error


def _fix_errors(output_dir: str, max_attempts: int = 3) -> None:
    """Run the app, parse errors, send to LLM for fixing, repeat."""
    output_path = Path(output_dir).resolve()

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Fix attempt {attempt}/{max_attempts} ---")
        errors = _smoke_test(output_dir)
        if not errors:
            print("App runs clean. All errors fixed.")
            return

        stderr = "\n".join(errors)
        parsed = _parse_traceback(stderr)
        if not parsed:
            print(f"Could not parse errors from:\n{stderr[:500]}")
            return

        print(f"Found {len(parsed)} error(s):")
        for e in parsed:
            print(f"  {Path(e['file']).name}:{e['line']} - {e['error']}")

        agent = SimpleAgent(max_failures=3)
        agent._system_prompt = (
            "You are a Python debugging expert. Fix the error in the source code.\n"
            "Use file_read to read the file, then file_edit to fix it.\n"
            "Only fix the specific error. Do not refactor or change unrelated code."
        )
        agent.register_tool(ReadTool(working_dir=output_dir))
        agent.register_tool(EditTool(working_dir=output_dir))
        agent.register_tool(GrepTool(working_dir=output_dir))
        agent.register_tool(BashTool(working_dir=output_dir, timeout=30))

        for err in parsed:
            filepath = err["file"]
            filename = Path(filepath).name
            prompt = (
                f"Fix this error in {filename} at line {err['line']}:\n"
                f"Error: {err['error']}\n\n"
                f"Read the file first, identify the bug, and fix it with file_edit."
            )
            print(f"\nFixing {filename}:{err['line']}...")
            agent.reset()
            agent.run(prompt, max_steps=5)

    errors = _smoke_test(output_dir)
    if errors:
        print(f"\nWarning: {len(errors)} error(s) remain after {max_attempts} fix attempts")
        for e in errors[:5]:
            print(f"  {e}")
    else:
        print("App runs clean after fixes.")


def main():
    parser = argparse.ArgumentParser(description="Build an app using DevWorkflow")
    parser.add_argument("requirement", nargs="?", default="requirement.txt",
                        help="Requirement file (default: requirement.txt)")
    parser.add_argument("--retry", action="store_true",
                        help="Retry only failed tasks from the latest report")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix runtime errors by sending them to the LLM")
    parser.add_argument("--max-steps", type=int, default=8,
                        help="Max steps per task (default: 8)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Max auto-retry rounds after execute (default: 3)")
    parser.add_argument("-o", "--output-dir",
                        help="Output directory (default: demo/<spec-stem>)")
    parser.add_argument("--show-report", action="store_true",
                        help="Show the latest report for this task")
    parser.add_argument("--list-reports", action="store_true",
                        help="List all reports for all tasks")
    args = parser.parse_args()

    # --list-reports: scan all demo dirs for reports
    if args.list_reports:
        _list_all_reports()
        return

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
    output_dir = args.output_dir or f"demo/{stem}"
    report_dir = Path(output_dir) / ".reports"

    # --show-report: display the latest report and exit
    if args.show_report:
        _show_report(report_dir)
        return

    # --fix: auto-fix runtime errors
    if args.fix:
        print("=" * 60)
        print(f"Auto-fixing errors for: {output_dir}")
        print("=" * 60)
        _fix_errors(output_dir)
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Interactive path confirmation (only for full runs)
    if not args.retry:
        print(f"\nProject will be created at: {Path(output_dir).resolve()}/")
        confirm = input("Use this path? [Y/n/custom path]: ").strip()
        if confirm and confirm.lower() not in ("y", "yes", ""):
            if confirm.lower() not in ("n", "no"):
                output_dir = confirm
            else:
                output_dir = input("Enter output directory: ").strip()
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

    wf = DevWorkflow(agent, report_dir=f"{output_dir}/.reports", working_dir=output_dir)

    if args.retry:
        # Retry mode: re-plan, then retry only failed tasks
        print("=" * 60)
        print(f"Retrying failed tasks for: {stem}")
        print("=" * 60)

        wf.plan_task(requirement)
        wf.decompose(requirement)
        wf.define_contracts(requirement)

        # Read the latest report to find failed tasks
        report_dir = Path(output_dir) / ".reports"
        reports = sorted(report_dir.glob("report_*.md"))
        if not reports:
            print("No previous reports found. Run without --retry first.")
            sys.exit(1)

        latest = reports[-1].read_text(encoding="utf-8")
        import re
        failed_nums = [int(m) for m in re.findall(r"- \[ \] Task (\d+):", latest)]

        if not failed_nums:
            # Also try finding "failed" in task status column
            failed_nums = [int(m) for m in re.findall(r"Task (\d+):.*\| failed \|", latest)]

        if not failed_nums:
            print("No failed tasks found. All tasks completed successfully.")
            sys.exit(0)

        print(f"Failed tasks to retry: {failed_nums}")
        # Initialize all as completed, mark failed ones
        wf._task_results = [{"index": i + 1, "task": t.description, "status": "completed", "result": "", "steps": 0, "failures": 0, "retry_count": t.retry_count}
                           for i, t in enumerate(wf._tasks)]
        for num in failed_nums:
            idx = num - 1
            if idx < len(wf._task_results):
                wf._task_results[idx]["status"] = "failed"

        _run_retry(wf, args.max_steps)
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

        # Auto-retry failed tasks
        failed = wf.failed_task_indices
        if failed and wf.report.status != "paused":
            for retry_round in range(1, args.max_retries + 1):
                failed = wf.failed_task_indices
                if not failed:
                    break
                print()
                print("=" * 60)
                print(f"Auto-retry round {retry_round}: {len(failed)} failed tasks")
                print("=" * 60)
                _run_retry(wf, args.max_steps)

            failed = wf.failed_task_indices
            if failed:
                print(f"\nWarning: {len(failed)} tasks still failing after {args.max_retries} retries")

        # Smoke test: run the app to check for startup errors
        if wf.report.status != "paused":
            print()
            print("=" * 60)
            print("Phase 4: Smoke Test")
            print("=" * 60)
            errors = _smoke_test(output_dir)
            if errors:
                print(f"Found {len(errors)} error(s) at startup:")
                for err in errors[:10]:
                    print(f"  {err}")
                print(f"\nTo auto-fix these errors, run:")
                print(f"  python build_with_workflow.py {args.requirement} --fix")
            else:
                print("App starts successfully.")

    # Final summary
    print()
    if wf.report:
        print(f"Report status: {wf.report.status}")
        print(f"Total steps: {wf.report.total_steps}, Failures: {wf.report.failed_steps}")

    if wf.report.status == "paused":
        print("\n>>> Agent paused. To resume:")
        print(">>> wf.resume('your guidance here')")

    # Project location and start instructions
    output_path = Path(output_dir).resolve()
    print(f"\n{'=' * 60}")
    print(f"Project location: {output_path}")
    print(f"{'=' * 60}")

    main_py = output_path / "main.py"
    app_py = output_path / "app.py"
    if main_py.exists():
        print(f"\nTo start the project:")
        print(f"  cd {output_path}")
        print(f"  python main.py")
    elif app_py.exists():
        print(f"\nTo start the project:")
        print(f"  cd {output_path}")
        print(f"  python app.py")
    else:
        py_files = sorted(output_path.glob("*.py"))
        if py_files:
            print(f"\nPython files in project:")
            for f in py_files:
                print(f"  {f.name}")


if __name__ == "__main__":
    main()
