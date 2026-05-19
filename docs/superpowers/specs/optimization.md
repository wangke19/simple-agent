# Prompt Optimization

> Originally: 2026-05-02-three-layer-prompt-optimization.md

---

## Three-Layer Prompt Optimization

After fixing task decomposition granularity (50 → 23 tasks), a full build completed successfully with GLM 5.1:
- 23 tasks, 22 passed, 1 skipped
- 402 total steps, 1 failure (bash timeout)
- Smoke test passed

But analysis revealed three layers of waste that could be eliminated.

### Layer 1: Plan → Decompose Mismatch

**Observation**: Plan phase produced 38 items. Decompose phase merged them into 23 tasks.

| Phase | Items | Examples of over-splitting |
|-------|-------|---------------------------|
| Plan | 38 | Tasks 1-5: one table per task. Task 26: dialog, Task 27: tab table, Task 28: tab filters |
| Decompose | 23 | Merged schema into 1 task, merged book_service methods into 1 task |

The plan phase used the old prompt ("Each task should be independent, verifiable, and small") while decompose had been updated to functional granularity. Decompose spent effort merging items that should never have been split.

**Root cause**: `plan_prompt` still said "small" while `decompose_prompt` said "functional." Two prompts out of sync.

**Fix**: Aligned plan_prompt with functional granularity:

Changed from:
```
"Each task should be independent, verifiable, and small"
```
To:
```
"Each task should represent one complete functional unit (e.g. one service with all methods,
 one UI component with its dialogs, one schema file with all tables).
 Target 15-25 tasks total. Do NOT split one file's functionality across multiple tasks.
 Do NOT include separate verification/testing tasks — each task validates itself."
```

Now plan and decompose phases speak the same language. Plan should produce ~20-25 items that decompose uses with minimal merging.

### Layer 2: Verification-Only Tasks Survive

**Observation**: Task 23 was "Create run_smoke_test.py automated verification script." Skipped after 3 retries. The decompose prompt said "Do NOT create verification-only tasks" but the language was a single bullet point — easy to overlook.

The build system already has: Phase 4 smoke test, Phase 5 import validation, schema validation. A separate smoke test script task is redundant.

**Root cause**: Anti-verification guidance buried in a bullet list alongside merge rules. LLM treated it as optional advice.

**Fix**: Strengthened decompose anti-verification language to a dedicated CRITICAL RULES block:

```
CRITICAL RULES:
- Do NOT create smoke test, verification, or testing tasks. The build system handles verification automatically.
- Do NOT create 'Verify xxx works' or 'Run tests for yyy' tasks. Every task validates its own output inline.
- The LAST task should be the application entry point (main.py / app.py / main_window.py).
```

Three changes: structural prominence (dedicated section vs buried bullet), explicit examples ("Verify xxx works"), replacement guidance ("LAST task should be entry point").

### Layer 3: Redundant File Reads in Late-Stage Tasks

**Observation**: Tasks 35-37 each read ALL 25 project files before writing verification scripts.

```
Task 35: 25 file_reads + 12 file_writes = 37 steps
Task 37: 25 file_reads + 12 file_writes = 37 steps
```

Total: ~75 file_read calls to re-read files already verified by their creation tasks.

The agent system prompt had no efficiency guidance. The LLM didn't know that rules, schema, and contracts are already injected into every task prompt. It defaulted to "read everything" — reasonable without constraints.

**Root cause**: System prompt gave no efficiency guidance.

**Fix**: Added efficiency rules to agent system prompt:

```
Efficiency rules:
- The task prompt already includes project rules, schema, and API contracts. Do NOT re-read AGENT.md or schema files.
- Only read files directly relevant to the current task (e.g. read book_service.py only if you're modifying it).
- Do NOT read all project files at the start of each task. Read only what you need.
- Validate your output with a quick syntax check or import test, then stop. Do not over-verify.
```

Four rules targeting four specific wasteful behaviors observed in the report.

### Expected Impact

| Metric | Before | After (expected) | Change |
|--------|--------|-------------------|--------|
| Plan items | 38 | ~20 | Plan starts at right granularity |
| Decomposed tasks | 23 | ~20 | No verification tasks |
| Total steps | 402 | ~300 | Eliminate redundant file_reads |
| Redundant file_reads | ~75 | ~0 | Efficiency guidance prevents re-reading |

### Lessons

1. **Prompts must be internally consistent.** When plan_prompt says "small" but decompose_prompt says "functional," decompose wastes effort merging items that shouldn't have been split. All pipeline prompts must share the same granularity definition.

2. **Guidance buried in a list is guidance ignored.** A single "Do NOT" bullet among 4 merge rules was insufficient. Critical rules need structural prominence (dedicated section, multiple bullets, concrete examples).

3. **The system prompt is an efficiency contract.** Without telling the LLM what's already provided (rules, schema, contracts) and what's expected (read only relevant files), it defaults to safest behavior: read everything. A few lines of guidance can eliminate hundreds of wasted API calls.

4. **Three layers, three prompts, one principle.** Plan prompt defines WHAT to build. Decompose prompt defines HOW to order it. System prompt defines HOW to execute it. All three should reinforce: functional, self-contained, no redundancy.

### Files Changed

- `src/simple_agent/prompts.py` — updated `plan_prompt` (English + Chinese), strengthened `decompose_prompt` (English + Chinese)
- `build_with_workflow.py` — added efficiency rules to agent system prompt
