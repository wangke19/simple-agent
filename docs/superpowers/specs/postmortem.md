# Postmortems

Integrated from individual postmortem specs (2026-04-30 to 2026-05-03).

---

## 1. Project Scaffold & Framework Rules — Design vs Practice

> Date: 2026-04-30

### Problem Origin

Running `python build_with_workflow.py demo/books-library-mgmt-design.md` produced code with runtime errors:

```
AttributeError: type object 'QTabWidget' has no attribute 'North'
```

**Root cause**: PRD specified "PyQt6 ONLY" but LLM output PyQt5-style enum syntax (`QTabWidget.North` instead of `QTabWidget.TabPosition.North`).

Three-layer problem:
1. **Design doc constraint granularity insufficient** — only said "PyQt6 ONLY", didn't specify scoped enum syntax
2. **Contracts only covered API signatures** — UI Framework Rules not translated into contracts
3. **Execution prompt chain lost original constraints** — `task.description + schema_block + contract_block`, no rules layer

Core gap: workflow had `schema_block` and `contract_block` but no `rules_block`.

### Implementation

Design decisions documented in [design.md Section 3](design.md#3-scaffold-rules--constraint-pipeline). 7 atomic commits covering: framework rules knowledge base, scaffold module, rules injection, workflow integration, guard checks, CLI integration, report enhancement.

### Lessons

- **Vibe coding core tension**: LLM has creative freedom, but engineering projects need discipline. Key is establishing correct constraint boundaries — skeleton enforced by engine, rules via prompt, implementation by LLM.
- **Framework pitfall knowledge base is essential.** LLM training data contains outdated code (PyQt5, Pydantic v1). Saying "use PyQt6" is insufficient — specific breaking changes must be written out.
- **Two-layer AGENT.md is universally applicable.** Any AI code generation tool needs: (1) tool's own engineering standards (universal, fixed) and (2) per-project constraints (extracted from design docs, dynamic).

---

## 2. Missing Dialog Modules + Tool Error Tolerance

> Date: 2026-05-02

### Incident 1: Missing Dialog Modules

**Symptom**: App crashes at runtime when clicking "Add Book" or "Add Member":

```
catalog_tab.py:216 → ModuleNotFoundError: No module named 'src.ui.book_dialog'
members_tab.py:179 → ModuleNotFoundError: No module named 'src.ui.member_dialog'
```

Files `book_dialog.py` and `member_dialog.py` were never created.

**Root cause** — three-layer constraint failure:

**Layer 1: Decompose** — tasks never created the files. Decomposition split by functional module (per-tab), not by file dependency graph. No task for `book_dialog.py` or `member_dialog.py`.

**Layer 2: Execute** — soft constraint ignored. AGENT.md specified `*_dialog.py → src/ui/` in directory layout, but the LLM used this as *justification* for writing `from src.ui.book_dialog import BookDialog` without creating the file. Rule was descriptive (what structure looks like), not prescriptive (what you must do).

**Layer 3: Validate** — blind spot. Four validation phases all missed this. Import checks only verified files modified by task, not whether their imports resolve. Lazy imports (inside event handlers) passed the smoke test since they only fire on button click.

**Why the LLM's mental model is wrong**: The LLM treats decomposition as "each task = one file". When writing `catalog_tab.py`, it assumes `book_dialog.py` will be created "later" by another task — but no such task exists.

**Fixes**:

1. **Hard constraint — Phase 5 static import validation**: `_validate_imports_exist()` scans all `.py` files for project-internal imports (`from src.xxx import yyy`) and checks target module exists. Runs after every task. Missing modules cause task failure, triggering auto-retry with error message.

2. **Soft constraint — AGENT.md Import Completeness rule**: Added imperative rule — "Every `from src.xxx import Yyy` MUST point to a file that already exists. If your task needs a dialog, create it in the SAME task or inline it."

### Incident 2: LLM Tool Input Errors

**Symptom**: 2 tool execution failures in build report (323 total steps, self-corrected):

```
file_read(Tool error: File not found: src/services)
file_grep(Tool error: Not a directory: src/ui/checkouts_tab.)
```

**Root cause**: LLM occasionally generates malformed tool inputs — passes directory path to file_read, appends trailing punctuation to file paths. Self-recoverable but each wasted step costs an API call.

**Fixes**:

1. **Tool-level path sanitization**:
   - ReadTool: strip trailing `/` and `.`, if directory list files, if not found suggest similar filenames (fuzzy match)
   - GrepTool: strip trailing `.`, if file suggest searching parent directory

2. **Increased retry budget**: `--max-retries` default 3 → 5

### Lessons

1. **Descriptive rules ≠ prescriptive rules.** Showing directory layout tells LLM what structure looks like, not what it must create. Every rule needs an imperative: "you MUST do X" not "the structure includes X".
2. **Lazy imports evade smoke tests.** Runtime-only imports pass startup checks. Static analysis (import resolution) is needed.
3. **Decomposition doesn't trace forward dependencies.** Files referenced by other files may fall through. Post-execution validation is the safety net.
4. **Soft + hard constraints need each other.** AGENT.md rules (soft) reduce error rate. Phase 5 validation (hard) catches what slips through. Neither alone is enough.
5. **Tool errors should help the LLM self-correct.** "is a directory, files are: ..." or "did you mean: ..." lets LLM correct in one step. Tool error messages are part of the feedback loop.
6. **Self-recoverable errors still cost API calls.** Path sanitization at tool layer is cheap; wasted LLM steps are expensive.

### Files Changed

- `src/simple_agent/dev_workflow.py` — added `_validate_imports_exist()` (Phase 5), 3 unit tests
- `src/simple_agent/scaffold.py` — added Import Completeness rule to AGENT.md template
- `src/simple_agent/tools/file_read.py` — path sanitization, directory hints, similar file suggestions
- `src/simple_agent/tools/file_grep.py` — path sanitization, file-as-directory hints
- `build_with_workflow.py` — `--max-retries` default 3 → 5

---

## 3. Task Decomposition Granularity

> Date: 2026-05-02

### Symptom

Build paused at task 6/50 with 3 consecutive `file_read` failures. Only 5 tasks completed, 45 remaining. Smoke test fails because `src/app.py` is empty (tasks 41-43 not reached).

```
Task 6 step 3: file_read(src/services/book_service.py) → FAILED (file not found)
Task 6 step 4: file_read(src/services/member_service.py) → FAILED (file not found)
Task 6 step 5: file_read(src/services/settings_service.py) → FAILED (file not found)
→ max_failures=3 triggered, agent paused
```

### Root Cause

The decomposition prompt defined "small" as "one file write or one command execution", producing 50 tasks for a library management app.

| Task Type | Count | Example |
|-----------|-------|---------|
| Schema (tables, indexes, triggers, defaults) | 4 | One table per task |
| DB manager + verification | 2 | Create + verify as separate tasks |
| Services (per-method) | 17 | CRUD, filtering, deletion guard as separate tasks |
| UI views (per-feature) | 20 | Dialog, tab table, tab filters as separate tasks |
| Smoke tests | 6 | Individual test scenarios |

**Why Task 6 failed**: Task 6 tried to verify `execute_read()` by reading service files that don't exist yet. Services are created in tasks 8-24. This is a **verification-before-dependency** problem.

**Three structural problems**:
1. One-file-per-task splits related work
2. Verification tasks separate from creation tasks
3. No target count guidance — more tasks = more compliant

### Fixes

**Fix 1: Redefine task granularity** — changed decompose prompt from "one file write" to "one complete feature", added target count (15-25 tasks), merge rules, banned verification-only tasks, self-contained requirement. See [optimization.md](optimization.md) for full prompt changes and further refinement.

**Fix 2: Increase max_steps_per_task (8 → 12)**. Larger functional tasks need more steps.

### Lessons

1. **"One file write" is not a useful task size.** Real development clusters by feature, not file.
2. **Verification tasks are an anti-pattern in decomposition.** Validation belongs inside the creation task, not as a separate task.
3. **LLMs need a target count.** Without numerical guidance, "small" means "as small as possible."
4. **Self-contained is the critical property.** A task that imports from files created by other tasks is fragile.
5. **Prompt wording matters more than model capability.** A better prompt on a weaker model outperforms a bad prompt on a stronger model.

### Files Changed

- `src/simple_agent/prompts.py` — rewrote `decompose_prompt` (English + Chinese)
- `build_with_workflow.py` — `--max-steps` default 8 → 12

---

## 4. Scaffold Role Boundary — Structure vs Implementation

> Date: 2026-05-03

### Symptom

Demo app crashes on startup with `sqlite3.OperationalError: no such table: settings`. The `db_manager.initialize_database()` method returns `True` but creates zero tables.

### Root Cause

**Direct cause**: `initialize_database()` searches for schema files in order:
1. `src/database/schema.sql` — found (0 bytes, empty) → uses this, nothing to execute
2. `database_init.sql` — skipped (already "found" a file)

Empty scaffold placeholder wins the search.

**Why the LLM created a different file**: AGENT.md says schema goes in `src/database/schema.sql`. PRD says "Create `database_init.sql`". LLM follows PRD, then copies to `schema.sql` — but empty scaffold file already exists.

**Why the LLM replaced scaffold code**: Scaffold pre-built `db_manager.py` with `initialize_schema()` method. LLM's `main_window.py` calls `initialize_database()` (different name). LLM rewrote `db_manager.py` entirely, ignoring the scaffold version.

**The deeper issue**: Scaffold overreached into implementation (see [design.md Section 3](design.md#3-scaffold-rules--constraint-pipeline) for the correct scope). When scaffold provides code with specific APIs, the LLM will rewrite it to match its own mental model. Empty placeholder files (`schema.sql`) are traps — they pass existence checks but provide no data.

### Fixes

**Fix 1: Scaffold provides structure only**. Removed pre-built `db_manager.py` and empty `schema.sql`. Scaffold now only creates directories, `__init__.py` files, entry point, and config files. LLM creates all `.py` implementation files from scratch.

**Fix 2: Updated AGENT.md template**. Changed from "db_manager.py is pre-built with initialize_schema()" (false claim) to "db_manager.py must include schema initialization" (requirement statement).

**Fix 3: LLM info output at startup**. Added `LLM Provider: glm | Model: glm-4.7 | Base URL: ...` to help debug which LLM is actually being used.

### Lessons

1. **Scaffold = structure, not implementation.** When scaffold provides code with specific APIs, LLM will rewrite it to match its own mental model, creating coupling that breaks.
2. **Empty placeholder files are traps.** They pass `path.exists()` checks but provide no data. Never create empty files that will be filled by later tasks.
3. **"Pre-built" claims in AGENT.md are lies.** Telling LLM "just call existing methods" doesn't work — it will rewrite the file anyway. State requirements, not prescriptions.
4. **Test actual build output, not just the pipeline.** Scaffold tests checked `db_manager.py exists()` — which passed even when the file was empty or contained scaffold code instead of LLM code.
5. **Environment variables override config files silently.** `ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7` overrode config file's `glm-5.1` with no error.

### Files Changed

- `src/simple_agent/scaffold.py` — removed pre-built `db_manager.py` and empty `schema.sql`, updated AGENT.md template
- `tests/unit/test_scaffold.py` — updated: `db_manager.py` should NOT exist after scaffold
- `build_with_workflow.py` — added LLM configuration output at startup
