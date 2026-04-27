# Workflow Retry Boundary Design

## Problem

1. **Task completion tracking is broken**: `_run_retry()` is called but never defined in `build_with_workflow.py`, crashing at runtime. Tasks with failed steps get marked `"completed"` if the agent eventually returns text, so `--retry` can't find failed tasks.
2. **Not fully automatic**: Running + retrying requires manual intervention (running `--retry` separately).
3. **No retry boundary**: Failed tasks retry indefinitely. Need a limit (3 retries per task) with dependency-aware pause/skip behavior.

## Design

### 1. TaskItem dataclass

Replace the flat `list[str]` task list with a structured model:

```python
@dataclass
class TaskItem:
    index: int          # 1-based
    description: str
    depends_on: list[int] = field(default_factory=list)  # 0-based indices
    retry_count: int = 0
    status: str = "pending"  # pending / completed / failed / skipped
```

`DevWorkflow._tasks` becomes `list[TaskItem]`. This gives per-task retry tracking and dependency info. The existing `failed_task_indices` property checks `status not in ("completed", "skipped")`.

### 2. Dependency-annotated decompose

Modify the decompose prompt to instruct the LLM to annotate each task with dependencies:

```
For each task, also specify its dependencies (which tasks must complete first).
Format: N. Task description [depends: 1, 3]
If no dependencies, write [depends: none]
```

Update `_parse_tasks` to extract `[depends: ...]` annotations and return `list[TaskItem]`. Fallback: if the LLM omits a dependency annotation, default to depending on the previous task (sequential assumption).

### 3. Execution with retry boundary

During `execute()`, for each task:

1. Run the agent as before
2. If the task fails (has failed steps), increment `retry_count`
3. If `retry_count >= 3`:
   - Check if any remaining pending task has this task in its `depends_on`
   - If yes → **pause** workflow, save state, prompt for manual intervention
   - If no → **mark as skipped**, continue to next task
4. If `retry_count < 3` → task stays failed, gets retried in the auto-retry loop

`retry_failed()` also increments `retry_count` on failure and applies the same >= 3 boundary check. The auto-retry loop in `build_with_workflow.py` drives this: after `execute()` completes, it calls `retry_failed()` in a loop for tasks with `retry_count < 3`. Tasks that hit the 3-retry limit are either skipped or cause a pause.

### 4. Fix `_run_retry` and `--retry` mode

- Define `_run_retry(wf, max_steps)` as a wrapper: calls `wf.retry_failed(max_steps_per_task=max_steps)` and prints the result.
- Fix `--retry` mode: instead of re-running plan/decompose/contracts (which generates a new task list that may not match the old report), load the previous workflow state from the saved report. Parse the task list from the report, restore `_task_results`, and retry only the failed ones.

### 5. Automatic full cycle

The full run flow:

```
plan → decompose (with dependencies) → contracts → execute → auto-retry loop (up to N rounds) → final report
```

No manual `--retry` needed for normal operation. The `--retry` flag becomes a recovery tool for loading a previous session's state.

## Files to modify

- `src/simple_agent/dev_workflow.py` — TaskItem, dependency parsing, retry boundary in execute/retry_failed
- `src/simple_agent/prompts.py` — decompose prompt with dependency annotation instruction
- `build_with_workflow.py` — define `_run_retry`, fix `--retry` mode, auto-retry loop
- `src/simple_agent/task_report.py` — no changes needed (already tracks per-step status)
