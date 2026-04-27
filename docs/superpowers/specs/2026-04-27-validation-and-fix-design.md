# Validation and Bug Fix Design

## Problem

The workflow has a fundamental gap: the agent writes code but never runs it. Each task is executed in isolation — the LLM generates a file, the agent considers it "done", and moves on. This causes:
- Import errors (PyQt5 vs PyQt6 mixed)
- Column name mismatches (SQL schema vs queries)
- Missing dependencies
- Runtime crashes on startup

## Design

### 1. Per-task import check (in DevWorkflow.execute)

After each task's `agent.run()` completes, before marking the task status:

1. Scan the agent's tool calls for any `file_write` operations
2. For each Python file written, run `python -c "import <module>"` in the working directory
3. If the import fails, log the error and mark the task as "failed"
4. The task stays in the failed list and gets retried in the auto-retry loop

This catches: import errors, syntax errors, PyQt version mismatches, missing dependencies.

Implementation: Add a `_validate_task_output` method to `DevWorkflow` that runs after each task in `execute()`. It uses `BashTool` to run import checks. If any check fails, the task status is set to "failed" regardless of what the agent reported.

### 2. Post-execution smoke test (in build_with_workflow.py)

After execute + auto-retry complete, before the final summary:

1. Find `main.py` or `app.py` in the output directory
2. Run `timeout 10 python main.py 2>&1` with `QT_QPA_PLATFORM=offscreen` for Qt apps
3. If it exits with a non-zero code (crash, not timeout), parse the traceback
4. If there are errors, print them and suggest running `--fix`

Implementation: Add a `_smoke_test` function to `build_with_workflow.py` called after the full run (but before the final summary). Returns a list of errors found.

### 3. `--fix` flag (in build_with_workflow.py)

When the user runs `python build_with_workflow.py spec.md --fix`:

1. Run the app, capture stderr
2. If errors found, parse the traceback (file, line, error message)
3. Read the relevant source files
4. Send to the LLM: "Fix this error in <file>: <traceback>\n\nSource:\n<file contents>"
5. Write the fixed file
6. Re-run the app to verify the fix works
7. Repeat up to 3 times
8. Print results

Implementation: Add a `_fix_errors` function to `build_with_workflow.py` that creates a SimpleAgent with the same tools, feeds it the error + source files, and loops until the app runs clean or 3 attempts are exhausted.

## Files to modify

- `src/simple_agent/dev_workflow.py` — add `_validate_task_output` method, call it in `execute()` and `retry_failed()`
- `build_with_workflow.py` — add `_smoke_test`, `_fix_errors`, `--fix` flag, call smoke test after full run
