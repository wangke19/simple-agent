# Simple-Agent Development Summary

## Stage 1: Prototype (17:27 - 17:49)

**4 commits** — From PRD to working code in ~20 minutes.

- Read the PRD (`simple-agent.prd`, a Chinese spec document)
- Created flat 3-file structure: `agent.py`, `main.py`, `test_agent.py`
- Used raw JSON parsing for tool calls (LLM returned JSON strings in text)
- Lambda-based tools: `search = lambda q: "北京晴天"` and `eval()` calculator
- Tests passed with mocked LLM responses

**Key characteristic**: Minimal, proof-of-concept. LLM tool calls were parsed as JSON from text blocks.

## Stage 2: Refactoring to Standard Package (17:49 - 18:00)

**2 commits** — From flat files to proper Python package.

- Restructured to `src/simple_agent/` with `pyproject.toml`
- Added `BaseTool` ABC, `ToolRegistry`, `AgentConfig`, `LLMClient`
- Proper error handling with custom exceptions
- Installed as editable package (`pip install -e .`)

**Key characteristic**: Proper software engineering structure, but still used the old JSON-in-text tool calling.

## Stage 3: Core Capabilities (18:25 - 19:17)

**7 commits** — Added the 6 capabilities planned in PRD Phase 2.

| Commit | Feature | What it added |
|--------|---------|---------------|
| `9ca2c37` | Native tool calling | Switched to Anthropic `tool_use` API — structured blocks instead of JSON parsing |
| `7b0b482` | File tools | ReadTool, WriteTool, EditTool, GrepTool with path sandboxing |
| `bc01b78` | Bash tool | BashTool with command denylist (rm -rf, mkfs, etc.) |
| `985f06e` | Multi-turn | Messages persist across `run()` calls, `reset()` to clear |
| `c4e89fd` | Memory | MemoryTool with `.agent/memory.md` persistence, loaded into system prompt |
| `1554427` | Context management | Compactor — LLM summarizes old messages when approaching token limit |

**Key characteristic**: Agent could now interact with the filesystem, run commands, and maintain long conversations. But it was still a single-step executor — no task planning or decomposition.

## Stage 4: First Real Task — Building an Inventory App (19:17 - 20:03)

**1 commit** — Tested the agent on a real development task.

- Ran agent to build a tkinter+SQLite purchase-sales-inventory app
- Generated `db.py` (362 lines) and `app.py` (407 lines) in `demo/inventory_app/`
- **Result**: Code compiled but had runtime errors
  - `get_purchases()` vs `get_all_purchases()` — method name mismatches
  - `add_product(name, category, price, stock)` vs `add_product(name, category, unit, price, stock)` — missing parameter
  - `purchase_product()` vs `add_purchase()` — completely wrong method names
- Required manual fixes to make it run

**Key characteristic**: Agent could generate code but lacked consistency across files. Each LLM call had no shared context with previous calls.

## Stage 5: Workflow & Quality Control (20:03 - 20:57)

**1 commit** — Added DevWorkflow to solve the consistency problem.

- **DevWorkflow**: `plan_task()` → `decompose()` → `execute()` with per-task `agent.reset()`
- **API Contracts**: New `define_contracts()` phase — LLM generates interface specs, injected into every task
- **Failure tracking**: `max_failures=3`, pauses with `TaskReport` on exceeded
- **TaskReport**: Markdown execution log with checklist
- **Pause/Resume**: Human-in-the-loop via `resume(guidance=...)`
- Re-ran the inventory task — **21/24 tasks passed**, no method name mismatches

**Key characteristic**: Agent could now plan, decompose, and maintain cross-task consistency. But everything was hardcoded in Chinese for a specific use case.

## Stage 6: Generalization (20:57 - 00:43)

**3 commits** — From a Chinese inventory builder to a general-purpose agent framework.

- **Prompts dataclass**: All LLM-facing prompts configurable with English defaults + `chinese_prompts()` factory
- **Messages dataclass**: All status/error messages configurable + `chinese_messages()` factory
- **WorkflowConfig**: `enable_plan`, `enable_decompose`, `enable_contracts` flags
- **retry_failed()**: Re-executes only failed tasks with file-reading context
- **Tool descriptions**: All 8 tools switched to English with constructor override
- **Requirement file**: Externalized from code — `python build_with_workflow.py my_task.md`
- **121 tests** (up from 103) covering all new features

**Key characteristic**: Fully configurable, language-agnostic framework. Any task, any language, any workflow configuration.

## Architecture Evolution

```
Stage 1-2:  User → Agent → LLM → JSON parse → Tool → Result
                (flat files, single turn)

Stage 3:    User → Agent → LLM → tool_use blocks → Tool → Result → Loop
                (structured tools, multi-turn, context compaction)

Stage 5:    Requirement → Plan → Decompose → Define Contracts → Execute(tasks)
                (workflow orchestration, shared API contracts, failure tracking)

Stage 6:    Requirement → [WorkflowConfig] → Plan → Decompose → Contracts → Execute
                (configurable prompts/messages, retry_failed, English defaults)
```

## Numbers

| Metric | Stage 1 | Stage 6 |
|--------|---------|---------|
| Source files | 3 | 17 |
| Lines of code | ~200 | ~1,700 |
| Tools | 2 (lambdas) | 8 (proper classes) |
| Tests | 3 | 121 |
| Languages | Chinese only | Configurable (English/Chinese) |
| Workflow | None | 4-phase with contracts |
| Error handling | None | max_failures, pause/resume, TaskReport |

## Key Lessons

1. **PRD-first works**: Starting from a written spec (PRD) gave clear direction and phased delivery
2. **Real tasks expose real problems**: The inventory app task revealed cross-task inconsistency that unit tests couldn't catch
3. **Contracts solve the multi-step consistency problem**: When each LLM call runs with fresh context, an explicit interface contract is the only way to keep outputs consistent
4. **Hardcoding is fine for prototyping, fatal for generalization**: Chinese strings, fixed prompts, and fixed workflow phases all needed extraction once the agent was used for different tasks
5. **Retry with context matters**: Simply re-running failed tasks doesn't work — the agent needs to read existing files first to write consistent code
