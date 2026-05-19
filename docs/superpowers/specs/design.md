# Design Specifications

Integrated from individual design specs (2026-04-27 to 2026-05-01).

---

## 1. Validation and Bug Fix System

> Originally: 2026-04-27-validation-and-fix-design.md

### Problem

The workflow has a fundamental gap: the agent writes code but never runs it. Each task is executed in isolation — the LLM generates a file, the agent considers it "done", and moves on. This causes:

- Import errors (PyQt5 vs PyQt6 mixed)
- Column name mismatches (SQL schema vs queries)
- Missing dependencies
- Runtime crashes on startup

### Design

#### 1.1 Per-task import check (in DevWorkflow.execute)

After each task's `agent.run()` completes, before marking the task status:

1. Scan the agent's tool calls for any `file_write` operations
2. For each Python file written, run `python -c "import <module>"` in the working directory
3. If the import fails, log the error and mark the task as "failed"
4. The task stays in the failed list and gets retried in the auto-retry loop

This catches: import errors, syntax errors, PyQt version mismatches, missing dependencies.

Implementation: Add a `_validate_task_output` method to `DevWorkflow` that runs after each task in `execute()`. It uses `BashTool` to run import checks. If any check fails, the task status is set to "failed" regardless of what the agent reported.

#### 1.2 Post-execution smoke test (in build_with_workflow.py)

After execute + auto-retry complete, before the final summary:

1. Find `main.py` or `app.py` in the output directory
2. Run `timeout 10 python main.py 2>&1` with `QT_QPA_PLATFORM=offscreen` for Qt apps
3. If it exits with a non-zero code (crash, not timeout), parse the traceback
4. If there are errors, print them and suggest running `--fix`

Implementation: Add a `_smoke_test` function to `build_with_workflow.py` called after the full run (but before the final summary). Returns a list of errors found.

#### 1.3 `--fix` flag (in build_with_workflow.py)

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

### Files

| File | Change |
|------|--------|
| `src/simple_agent/dev_workflow.py` | Add `_validate_task_output` method, call it in `execute()` and `retry_failed()` |
| `build_with_workflow.py` | Add `_smoke_test`, `_fix_errors`, `--fix` flag |

---

## 2. Workflow Retry Boundary

> Originally: 2026-04-27-workflow-retry-boundary-design.md

### Problem

1. **Task completion tracking is broken**: `_run_retry()` is called but never defined in `build_with_workflow.py`, crashing at runtime. Tasks with failed steps get marked `"completed"` if the agent eventually returns text, so `--retry` can't find failed tasks.
2. **Not fully automatic**: Running + retrying requires manual intervention (running `--retry` separately).
3. **No retry boundary**: Failed tasks retry indefinitely. Need a limit (3 retries per task) with dependency-aware pause/skip behavior.

### Design

#### 2.1 TaskItem dataclass

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

#### 2.2 Dependency-annotated decompose

Modify the decompose prompt to instruct the LLM to annotate each task with dependencies:

```
For each task, also specify its dependencies (which tasks must complete first).
Format: N. Task description [depends: 1, 3]
If no dependencies, write [depends: none]
```

Update `_parse_tasks` to extract `[depends: ...]` annotations and return `list[TaskItem]`. Fallback: if the LLM omits a dependency annotation, default to depending on the previous task (sequential assumption).

#### 2.3 Execution with retry boundary

During `execute()`, for each task:

1. Run the agent as before
2. If the task fails (has failed steps), increment `retry_count`
3. If `retry_count >= 3`:
   - Check if any remaining pending task has this task in its `depends_on`
   - If yes → **pause** workflow, save state, prompt for manual intervention
   - If no → **mark as skipped**, continue to next task
4. If `retry_count < 3` → task stays failed, gets retried in the auto-retry loop

`retry_failed()` also increments `retry_count` on failure and applies the same >= 3 boundary check. The auto-retry loop in `build_with_workflow.py` drives this: after `execute()` completes, it calls `retry_failed()` in a loop for tasks with `retry_count < 3`. Tasks that hit the 3-retry limit are either skipped or cause a pause.

#### 2.4 Fix `_run_retry` and `--retry` mode

- Define `_run_retry(wf, max_steps)` as a wrapper: calls `wf.retry_failed(max_steps_per_task=max_steps)` and prints the result.
- Fix `--retry` mode: instead of re-running plan/decompose/contracts (which generates a new task list that may not match the old report), load the previous workflow state from the saved report. Parse the task list from the report, restore `_task_results`, and retry only the failed ones.

#### 2.5 Automatic full cycle

The full run flow:

```
plan → decompose (with dependencies) → contracts → execute → auto-retry loop (up to N rounds) → final report
```

No manual `--retry` needed for normal operation. The `--retry` flag becomes a recovery tool for loading a previous session's state.

### Files

| File | Change |
|------|--------|
| `src/simple_agent/dev_workflow.py` | TaskItem, dependency parsing, retry boundary in execute/retry_failed |
| `src/simple_agent/prompts.py` | Decompose prompt with dependency annotation instruction |
| `build_with_workflow.py` | Define `_run_retry`, fix `--retry` mode, auto-retry loop |
| `src/simple_agent/task_report.py` | No changes needed (already tracks per-step status) |

---

## 3. Scaffold, Rules & Constraint Pipeline

> Merged from: 2026-04-30-project-scaffold-and-rules-design.md, 2026-04-30-constraint-validation-pipeline-design.md

### Problem

LLM-generated projects lack engineering discipline across multiple dimensions:

1. **Framework rules lost** — PRD says "PyQt6 ONLY" but LLM outputs PyQt5-style enum syntax (`QTabWidget.North` instead of `QTabWidget.TabPosition.North`). No mechanism to inject known framework pitfalls.
2. **No standard structure** — layout varies arbitrarily between runs.
3. **SQL doesn't match PRD Data Model** — generated `settings.key` instead of `settings.setting_key`; missing columns in `fines` table.
4. **Schema feedback loop** — once wrong SQL was generated, `_refresh_schema_block()` marked it as "GROUND TRUTH", causing downstream tasks to copy wrong column names. Error self-reinforced.

Root cause: the workflow has three injection points (task, schema, contract) but none carries framework rules, engineering standards, or Data Model constraints. Information is **structurally truncated** in the pipeline — not a context-window or hallucination issue.

### Solution Overview

Add a **Scaffold phase** and **multi-layer constraint system** to the DevWorkflow pipeline:

```
PRD → Scaffold → Plan → Decompose → Contracts → Execute(含守卫) → Report → Smoke Test
```

### Component 1: Two-Layer AGENT.md

**Layer 1: simple-agent AGENT.md** (fixed, ships with simple-agent)

Located at `src/simple_agent/agent_md_template.md`. Universal engineering discipline for ALL generated projects:
- Required project elements (entry point, dependency declaration, tests/, .gitignore)
- Quality gates (import check, schema validation, smoke test)
- Code standards (no placeholder code, no hardcoded secrets)

**Layer 2: Project AGENT.md** (dynamic, generated per project)

Located at `{project_root}/AGENT.md`. Generated by scaffold from:
- PRD Architecture section → framework and tech stack
- PRD Conventions/Rules sections → project-specific constraints
- PRD Data Model section → table/column definitions (parsed via `parse_data_model_columns()`)
- Framework rules knowledge base → known pitfalls for detected frameworks

### Component 2: Scaffold Phase

Positioned BEFORE Plan phase. Does NOT call LLM — pure structured operations:

1. **Parse PRD** — extract structured sections via regex/heading matching (Architecture, Conventions, Data Model, Rules)
2. **Create project skeleton** — directories, `__init__.py` files, entry point, config files (structure only, no implementation code)
3. **Generate project AGENT.md** — combine PRD rules + Data Model columns + detected framework pitfalls

**Framework Rules Knowledge Base:**

```
src/simple_agent/framework_rules/
├── pyqt6.md      # scoped enums, signal syntax, thread safety
├── flask.md      # session security, SQL injection
├── fastapi.md    # async pitfalls, Pydantic v2
├── react.md      # hooks rules, key prop
└── generic.md    # error handling, logging, security
```

Detection logic: scan PRD Architecture section for framework keywords. Always append generic.md.

**New Module: `scaffold.py`**

```python
@dataclass
class ScaffoldConfig:
    prd_path: str
    output_dir: str
    skip_scaffold: bool = False

@dataclass
class ScaffoldResult:
    output_dir: str
    agent_md_path: str
    detected_frameworks: list[str]
    rules_count: int
    original_agent_md: str = ""                    # snapshot for auto-restore
    required_sections: list[str] = field(...)      # sections that must be preserved

def run_scaffold(config: ScaffoldConfig) -> ScaffoldResult:
    """Phase 0: Create project skeleton and AGENT.md from PRD."""
```

Key functions:
- `parse_prd_sections(prd_text: str) -> dict[str, str]` — extract sections by heading
- `parse_data_model_columns(data_model_text: str) -> dict[str, list[str]]` — parse markdown tables to `{table: [columns]}`, pure regex
- `detect_frameworks(architecture_section: str) -> list[str]` — keyword matching
- `generate_agent_md(prd_sections: dict, frameworks: list[str]) -> str` — compose project AGENT.md with Data Model
- `create_skeleton(output_dir: str, frameworks: list[str], has_database: bool) -> None` — directories + config only
- `validate_agent_md_sections(path, required_sections, original_content) -> list[str]` — check integrity, returns errors

### Component 3: Four-Layer Constraint Protection

| Layer | Mechanism | Controller | Trigger |
|-------|-----------|-----------|---------|
| **Scaffold** | Data Model + rules written into AGENT.md | Engine-enforced | Phase 0 |
| **Pre-task** | AGENT.md section integrity validation + auto-restore from snapshot | Engine-enforced | Before each task |
| **Post-task** | PRD-aware SQL schema validation (`_validate_sql_against_prd()`) | Engine-enforced | After each task |
| **Schema block** | Mismatch warning injection if SQL ≠ PRD | Prompt injection | Each schema_block refresh |

**Prompt Injection:**

```python
rules_block = build_rules_block(project_agent_md, simple_agent_agent_md)
augmented_task = f"{task.description}{rules_block}{schema_block}{contract_block}"
```

Injection points: `execute()`, `resume()`, `retry_failed()`.

**Real-time Guard** — enhanced `_validate_task_output`:

| Check | Description | Failure behavior |
|-------|-------------|-----------------|
| AGENT.md integrity | Key sections not deleted/emptied (via `validate_agent_md_sections()`) | Auto-restore from snapshot, mark task failed |
| Forbidden import detection | Scan .py files for imports violating AGENT.md framework rules | Mark task failed + specific error |
| SQL vs PRD validation | `_validate_sql_against_prd()` compares generated SQL columns with PRD Data Model | Mark task failed |
| Directory guard | tests/ directory must exist | Mark task failed |
| Empty file check | No placeholder-only function bodies | Warning only |

**Schema Block Mismatch Warning:** If generated SQL doesn't match PRD, inject warning: "Generated SQL does NOT match PRD Data Model! The Data Model columns in AGENT.md are CORRECT." This breaks the feedback loop.

### Data Flow

```
PRD Data Model (full column definitions)
  → parse_data_model_columns() → {table: [columns]}
  → generate_agent_md() → AGENT.md ## Data Model section
  → _build_rules_block() → injected into every task prompt

Before each task:
  validate_agent_md_sections() → auto-restore from snapshot if missing

After each task:
  _validate_sql_against_prd() → cross-validate generated SQL vs PRD columns

Schema block injection:
  If SQL ≠ PRD → append WARNING telling LLM to use AGENT.md Data Model
```

### CLI Changes

```bash
--skip-scaffold    # Skip scaffold phase (for existing projects)
```

### Files

| File | Change |
|------|--------|
| `src/simple_agent/scaffold.py` | **NEW** — scaffold phase, `parse_data_model_columns()`, `validate_agent_md_sections()`, Data Model in AGENT.md |
| `src/simple_agent/framework_rules/*.md` | **NEW** — framework pitfall knowledge base |
| `src/simple_agent/agent_md_template.md` | **NEW** — universal engineering standards template |
| `src/simple_agent/dev_workflow.py` | Add rules_block injection, guard checks, `_prd_table_columns`, `_validate_sql_against_prd()`, pre-task validation, schema mismatch warning |
| `src/simple_agent/prompts.py` | Add `rules_injection_template`, schema_injection_template Data Model priority |
| `build_with_workflow.py` | Add `--skip-scaffold` flag, call scaffold before plan |
| `src/simple_agent/messages.py` | Add scaffold + guard messages |

### Lessons

- **Schema feedback loops are worse than single errors.** Once wrong data is marked "ground truth", it propagates to all downstream files and validation becomes an error amplifier. Fix: inject correction signals into the feedback loop.
- **Scaffold snapshot makes AGENT.md immutable.** Any LLM modification (deletion, truncation) is auto-reversed. AGENT.md becomes an engine-controlled constraint source, not a modifiable file.
- **Check information flow end-to-end.** Starting from the final prompt, trace backward. Don't assume "PRD has constraints = LLM knows constraints."
- **Framework pitfall knowledge base is essential.** LLM training data contains outdated code. Saying "use PyQt6" is insufficient — specific breaking changes must be written out.
- **Three-layer constraint model:** skeleton (engine-enforced), rules (prompt-injected), implementation (LLM free reign).

---

## 5. Skill Call System

> Originally: 2026-04-30-skill-call-design.md

### Overview

Add prompt-based skill calling. Skills are named prompt templates that inject specialized instructions into the agent's conversation. The LLM decides when to activate a skill by calling a `use_skill` tool.

### Approach: Skill as a Tool

Register a `use_skill` tool in the existing `ToolRegistry`. When the LLM calls it, the tool loads the skill's prompt content and returns it as a tool result. The LLM then follows the skill's instructions.

### Skill File Format

Markdown files with YAML frontmatter in a `skills/` directory:

```markdown
---
name: brainstorming
namespace: superpowers
description: >
  Use before any creative work. Explores user intent and requirements before implementation.
---

[Skill prompt body — instructions injected when activated]
```

- `namespace` is optional. `namespace` + `name` = full skill ID (e.g., `superpowers:brainstorming`)
- `description` shown to LLM in tool description to help it decide when to use the skill
- Files auto-discovered recursively from `skills/` directory

### Module Structure

```
src/simple_agent/skills/
├── __init__.py       # Public exports (SkillRegistry, Skill, UseSkillTool)
├── registry.py       # SkillRegistry - loads and manages skills
├── loader.py         # Parses skill Markdown files (frontmatter + body)
└── tool.py           # UseSkillTool - BaseTool subclass for skill activation
```

### Components

**SkillRegistry** — `SkillRegistry(skills_dir: Path)`, scans on init. Methods: `get(skill_id)`, `list_skills()`, `skill_descriptions()`.

**Skill** (dataclass) — `name`, `namespace`, `description`, `content`, `full_id` (computed), `source_path`.

**Skill Loader** — `load_skill(path)`, parse frontmatter + body using `pyyaml`. Validates required fields.

**UseSkillTool** — extends `BaseTool` with `name = "use_skill"`. Parameters: `skill_name` (required), `args` (optional). Returns formatted skill content. Dynamic description includes available skills.

### Agent Integration

No changes to `agent.py` core loop. The `UseSkillTool` is registered like any other tool:

```python
skill_registry = SkillRegistry(skills_dir=Path("skills"))
use_skill_tool = UseSkillTool(skill_registry=skill_registry)
agent.register_tool(use_skill_tool)
```

### Agent Flow

1. LLM sees `use_skill` tool with available skill descriptions
2. LLM calls `use_skill(skill_name="superpowers:brainstorming")`
3. `UseSkillTool.execute()` loads skill content from `SkillRegistry`
4. Formatted prompt returned as tool result string
5. LLM processes the skill instructions and follows them
6. Conversation continues with skill instructions in context

### Testing Strategy

- Unit tests for `SkillLoader`: frontmatter parsing, missing fields, empty body
- Unit tests for `SkillRegistry`: loading, lookup by full ID / short name, duplicate detection
- Unit tests for `UseSkillTool`: skill activation, unknown skill error, args passing
- Integration test: agent with skill tool, verify content flows through conversation

### Dependencies

- `pyyaml` for YAML frontmatter parsing

---

## 6. LLM Provider Switching

> Originally: 2026-05-01-llm-provider-switching-design.md

### Overview

Add environment variable `LLM_PROVIDER` to switch between LLM providers without code changes.

### Providers

| LLM_PROVIDER | Base URL | Model |
|--------------|----------|-------|
| `glm` | `https://open.bigmodel.cn/api/anthropic` | `glm-4.7` |
| `minimax` | `https://api.minimaxi.com/anthropic` | `MiniMax-M2.7` |

### Usage

```bash
LLM_PROVIDER=glm     # ZhiPu GLM
LLM_PROVIDER=minimax # MiniMax
```

### Priority

1. `ANTHROPIC_BASE_URL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` (explicit override, highest)
2. `LLM_PROVIDER` preset (convenience switch)
3. Hardcoded defaults (fallback)

### Files

| File | Change |
|------|--------|
| `src/simple_agent/config.py` | Parse `LLM_PROVIDER`, apply preset defaults |
| `.env.example` | Document `LLM_PROVIDER` and presets |
