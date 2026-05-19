# LLM Provider Comparison

> Originally: 2026-05-03-llm-provider-comparison.md

---

## GLM 4.7 vs GLM 5.1 vs MiniMax-M2.7

### Test Setup

**Task:** Build a Library Management System (PyQt6 + SQLite) from a PRD spec.
**Pipeline:** scaffold → plan → decompose → contracts → execute → report
**Max retries:** 5

### Results Summary

| Metric | GLM 4.7 (old prompts) | GLM 4.7 (new prompts) | GLM 5.1 | MiniMax-M2.7 |
|--------|----------------------|----------------------|---------|-------------|
| **Prompt config** | "one file write" | Functional granularity | Functional granularity | Functional granularity |
| **Scaffold** | Pre-built db_manager | Pre-built db_manager | Structure only | Structure only |
| **Max steps/task** | 8 | 8 | 12 | 12 |
| **Status** | Paused (6/50) | Completed | **Completed** | Paused (16/20) |
| **Task count** | 50 | 23 | **21** | 20 |
| **Tasks completed** | 5/50 | 22/23 | **21/21** | 15/20 |
| **Total steps** | 43 (partial) | 402 | **133** | 195 (incomplete) |
| **Failures** | 3 (structural) | 1 (bash timeout) | **4** (self-recovered) | 13 (5 stuck) |
| **Smoke test** | Failed | Passed | 1 error (PyQt6 API) | Failed |
| **Steps/task avg** | ~8.6 | ~17.5 | **~6.3** | ~13.0 |

### Evolution Across Iterations

#### Phase 1: GLM 4.7 + Old Prompts (50 tasks, paused at 6)

Baseline run before optimization. Decompose prompt said "one file write or one command execution" producing 50 tasks.

**Why it failed:** Task 6 tried to verify `execute_read()` by reading service files that don't exist yet. 3 consecutive `file_read` failures triggered `max_failures=3`. Schema split across 5 tasks.

**Established need for:** functional granularity, no verification-only tasks, increased max_steps.

#### Phase 2: GLM 4.7 + New Prompts (23 tasks, completed)

Same model, updated decompose_prompt to functional granularity. All 23 tasks completed.

**Performance:** 402 total steps (~17.5 steps/task), 1 failure (bash timeout), smoke test passed. But late-stage tasks each read all 25 project files (75 redundant file_reads).

**Established need for:** efficiency guidance in system prompt, plan/decompose prompt alignment, anti-verification task rules.

#### Phase 3: GLM 5.1 + All Optimizations (21 tasks, completed)

All three prompt layers optimized. Scaffold reduced to structure-only.

**Performance:** 133 total steps (~6.3 steps/task), 4 failures all self-recovered. Only 1 smoke test error (PyQt6 `AA_UseHighDpiPixmaps` hallucination).

**Key improvement:** steps/task dropped from 17.5 (GLM 4.7) to 6.3 (GLM 5.1) — **64% reduction**.

#### Phase 4: MiniMax-M2.7 + Same Optimizations (20 tasks, paused at 16)

Same optimized prompts, different model.

**Performance:** 195 steps for 15 tasks (incomplete), 13 failures including task-level stalls. `checkout_tab.py` and `report_tab.py` never created.

**Why MiniMax failed:** higher per-task step consumption (13 vs 6.3), more context gathering (5-7 file_reads vs 2-3), XML artifacts in output, some tasks consumed all steps reading without producing output.

### Failure Patterns Across Models

| Failure Type | GLM 4.7 (old) | GLM 4.7 (new) | GLM 5.1 | MiniMax |
|-------------|:---:|:---:|:---:|:---:|
| Task stall (ran out of steps) | 1 | 0 | 0 | 4 |
| File not found (self-recovered) | 2 | 0 | 4 | 6 |
| Bash timeout | 0 | 1 | 0 | 1 |
| Dependency cascade | 1 | 0 | 0 | 3 |
| PyQt6 API hallucination | 0 | 0 | 1 | 0 |
| **Total failures** | **3** | **1** | **4** | **13** |
| **Structural failures** (blocked pipeline) | **1** | **0** | **0** | **5** |

Key insight: GLM 5.1 has more total failures (4) than GLM 4.7 new (1), but all are **transient** (self-recovered). MiniMax's 13 failures include 5 **structural** failures (permanently stuck). Transient failures are cheap; structural failures are fatal.

### Step Efficiency

```
Steps per task (lower is better):

GLM 5.1   ████████████░░░░░░░░░░  6.3  ★ best
GLM 4.7   ████████████████████████████████████░░  17.5  (new prompts, many redundant reads)
MiniMax   ████████████████████████████░░  13.0
GLM 4.7   ██████████████░░░░░░░░  8.6   (old prompts, only 5 tasks completed)
```

GLM 5.1's efficiency comes from: efficiency rules in system prompt, smarter context gathering (2-3 files not 5-7), direct execution pattern (read → write → validate → stop).

### Code Quality

| Aspect | GLM 4.7 | GLM 5.1 | MiniMax-M2.7 |
|--------|---------|---------|-------------|
| File naming consistency | Good | Good | Inconsistent |
| Architecture patterns | Clean | Clean (singleton, DI) | Verbose, inconsistent |
| Framework API accuracy | Good | 1 hallucination | Unknown (incomplete) |
| Output format compliance | Good | Good | XML artifacts |
| AGENT.md rule following | Partial | Good | Partial |
| Redundant file reads | High | Low | High |

### Root Cause of Performance Gap

**Factor 1: Prompt quality** (GLM 4.7 old → new: 50→23 tasks, paused→completed)

Prompt changes that mattered:
- "one file write" → "one complete feature" (task count halved)
- "small" → "Target 15-25 tasks" (granularity anchor)
- No verification tasks (eliminated fatal dependency issues)
- Efficiency guidance (steps/task: 17.5 → 6.3)

**Factor 2: Model capability** (GLM 4.7 → 5.1: 402→133 steps, 17.5→6.3 steps/task)

Same prompts, different model:
- GLM 5.1 follows efficiency guidance better
- Better step budget discipline (never stalls)
- Cleaner output format (no XML artifacts)

**Factor 3: Model weakness** (GLM 5.1 → MiniMax: completed→paused)

- MiniMax consumes more steps per task (13 vs 6.3)
- Stalls on complex tasks
- Produces format artifacts

### Framework Rules: Soft Constraints with Model-Dependent Effectiveness

| Error | GLM 4.7 | GLM 5.1 | MiniMax | Rule Exists? |
|-------|---------|---------|---------|-------------|
| `AA_UseHighDpiPixmaps` (PyQt5) | Never | Never | **Generated** | Yes |
| `WrapLongRect` (wrong enum) | Never | Never | **Generated** | Yes |
| Mixed PyQt5/PyQt6 imports | Never | Never | Never | Yes |

Framework rules (`pyqt6.md`) existed before all runs. GLM models followed them completely. MiniMax followed most but violated "PyQt6 ONLY" on specific APIs where training data has strong PyQt5 patterns.

**Implication:** Prompt engineering aligns structural behavior across models but cannot align **knowledge accuracy** — that's a training data property. For weaker adherence, add hard validation (post-task checks for deprecated APIs).

### Recommendations

1. **GLM 5.1 is the recommended provider.** Best step efficiency (6.3/task), 100% task completion, clean output.

2. **Prompt quality matters more than model capability for structural issues.** GLM 4.7 with good prompts (completed) beats GLM 5.1 with bad prompts (paused). Fix prompts first, then optimize model choice.

3. **Increase max_steps to 15 for MiniMax** if it must be used. 12 steps is borderline for complex UI components with 13 steps/task average.

4. **Framework rules are necessary but not sufficient.** They reduce errors for strong instruction-following models. For weaker models, add hard validation.

5. **Distinguish prompt-fixable vs model-fixable issues.** Task granularity, dependency ordering, step efficiency are prompt-fixable. Framework API hallucination is model-fixable. Invest in prompts first, then select model.

6. **Weaker models are valuable for pipeline stress-testing.** Most bugs were exposed by MiniMax, not GLM:

| Bug | Exposed by | Would GLM 5.1 find it? |
|-----|-----------|----------------------|
| Empty schema.sql placeholder trap | MiniMax | No |
| `AA_UseHighDpiPixmaps` hallucination | MiniMax | No |
| Task stalls without output | MiniMax | No |
| Framework rule adherence inconsistency | MiniMax | No |

**Recommended strategy:**
- **Daily development:** Best model (GLM 5.1) for fast iteration
- **Pre-release testing:** One build with weaker model to expose edge cases
- **CI:** No need for weaker models — reserve for manual checkpoints

This is analogous to fuzzing in traditional software: you don't run it on every commit, but before a release to find bugs that normal test cases miss.
