# Simple Agent

A minimal AI agent framework with tool-calling, multi-step workflows, and configurable prompts. Works with any Anthropic-compatible API (Anthropic Claude, ZhiPu glm, etc.).

## How It Works

```
User Task → Agent constructs prompt (tools + history) → LLM decides action
                       ↑                                       │
                       │                            ┌──────────┴──────────┐
                       │                            │                     │
                       │                        Tool Call             Direct Answer
                       │                            │                     │
                       │                     Execute Tool                 │
                       │                            │                     │
                       └──── Append result ─────────┘                     │
                                                                      ▼
                                                                 Return Result
```

## Quick Start

```bash
pip install -e .
cp .env.example .env   # edit with your API key
python main.py
```

## Configuration

Set environment variables in `.env`:

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_BASE_URL` | API base URL | `https://api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | API key (required) | — |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Model name | `claude-sonnet-4-20250514` |

## Basic Usage

```python
from dotenv import load_dotenv
from simple_agent import SimpleAgent
from simple_agent.tools import SearchTool, CalculatorTool

load_dotenv()

agent = SimpleAgent()
agent.register_tool(SearchTool())
agent.register_tool(CalculatorTool())

result = agent.run("What is 2^10 + 3*7?")
print(result)
```

## DevWorkflow: Build Applications from Requirements

### Step 1: Write a requirement file

Create a `.md` file describing what you want to build:

```markdown
# student_mgmt.md

Create a student registration management GUI app (tkinter + SQLite).

Requires: db.py (database layer with students/courses/grades tables CRUD),
app.py (GUI layer with 4 tabs: Student Management / Course Management /
Grade Entry / Grade Query).

Database schema:
- Students table: id, name, gender, birthday, class, phone
- Courses table: id, name, credits, teacher
- Grades table: id, student_id, course_id, score, semester
```

### Step 2: Run the workflow

```bash
python build_with_workflow.py student_mgmt.md
```

Output goes to `demo/student_mgmt/`. The workflow runs 4 phases:

1. **Plan** — LLM analyzes requirements and generates a task plan
2. **Decompose** — Breaks plan into atomic tasks (e.g., "Create db.py", "Add CRUD methods")
3. **Define Contracts** — Generates interface specs between modules so all tasks use consistent APIs
4. **Execute** — Runs each task sequentially, injecting the contract for consistency

### Step 3: Retry failed tasks

Some tasks may fail (timeout, complex UI). Retry only the failures:

```bash
python build_with_workflow.py student_mgmt.md --retry
```

The retry reads existing files first, then re-executes only failed tasks with full code context.

### Step 4: Run the generated app

```bash
cd demo/student_mgmt && python main.py
```

### Programmatic Usage

```python
from simple_agent import SimpleAgent, DevWorkflow
from simple_agent.tools import WriteTool, ReadTool, EditTool, GrepTool, BashTool

agent = SimpleAgent(max_failures=3)
agent.register_tool(WriteTool(working_dir="my_project"))
agent.register_tool(ReadTool(working_dir="my_project"))
agent.register_tool(EditTool(working_dir="my_project"))
agent.register_tool(GrepTool(working_dir="my_project"))
agent.register_tool(BashTool(working_dir="my_project"))

wf = DevWorkflow(agent, report_dir="my_project/.reports")

requirement = "Build a REST API with Flask and SQLite..."
wf.plan_task(requirement)
wf.decompose(requirement)
wf.define_contracts(requirement)
wf.execute(max_steps_per_task=8)

# Or use the convenience method
wf.run_all(requirement)
```

## Configurable Prompts & Messages

All prompts and messages have English defaults with full customization:

```python
from simple_agent import SimpleAgent, Prompts, Messages
from simple_agent.prompts import chinese_prompts
from simple_agent.messages import chinese_messages

# English defaults (default)
agent = SimpleAgent()

# Chinese backward compatibility
agent = SimpleAgent(prompts=chinese_prompts(), messages=chinese_messages())

# Custom prompts
prompts = Prompts(
    default_system_prompt="You are a Python expert...",
)
agent = SimpleAgent(prompts=prompts)
```

## Creating Custom Tools

```python
from simple_agent.tools.base import BaseTool

class TranslateTool(BaseTool):
    name = "translate"

    @property
    def _default_description(self) -> str:
        return "Translate text between languages."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "target_lang": {"type": "string", "description": "Target language"},
            },
            "required": ["text", "target_lang"],
        }

    def execute(self, **kwargs) -> str:
        return translated_text

agent.register_tool(TranslateTool())
```

## WorkflowConfig

Control which phases run:

```python
from simple_agent.dev_workflow import WorkflowConfig

# Skip contract generation for simple tasks
config = WorkflowConfig(enable_contracts=False, max_steps_per_task=12)
wf = DevWorkflow(agent, workflow_config=config)
```

## Built-in Tools

| Tool | Name | Description |
|------|------|-------------|
| `WriteTool` | `file_write` | Create or overwrite files |
| `ReadTool` | `file_read` | Read file contents with line range |
| `EditTool` | `file_edit` | Replace unique strings in files |
| `GrepTool` | `file_grep` | Search file contents with regex |
| `BashTool` | `bash` | Execute shell commands |
| `CalculatorTool` | `calculate` | Evaluate math expressions |
| `SearchTool` | `search` | Search for information (placeholder) |
| `MemoryTool` | `memory` | Save/recall cross-session info |

## Project Structure

```
src/simple_agent/
├── __init__.py        # Public API exports
├── agent.py           # SimpleAgent: decision loop with failure tracking & pause/resume
├── config.py          # AgentConfig dataclass from environment
├── llm_client.py      # Anthropic SDK wrapper
├── dev_workflow.py     # DevWorkflow, WorkflowConfig: plan → decompose → contracts → execute
├── prompts.py         # Prompts dataclass + chinese_prompts()
├── messages.py        # Messages dataclass + chinese_messages()
├── compactor.py       # Context window compaction via LLM summarization
├── task_report.py     # TaskReport: markdown execution log & checklist
├── exceptions.py      # AgentError, LLMError, ToolError
└── tools/
    ├── base.py        # BaseTool ABC
    ├── registry.py    # ToolRegistry
    ├── bash.py        # BashTool with command denylist
    ├── file_read.py   # ReadTool with path sandboxing
    ├── file_write.py  # WriteTool with auto-mkdir
    ├── file_edit.py   # EditTool with unique match enforcement
    ├── file_grep.py   # GrepTool with regex + glob
    ├── calculator.py  # CalculatorTool
    ├── search.py      # SearchTool (placeholder)
    └── memory.py      # MemoryTool with .agent/memory.md persistence
```

## Testing

```bash
python -m pytest tests/unit/ -v          # 121 unit tests (mocked LLM)
python -m pytest tests/integration/ -v   # Integration tests (real API)
```

## Requirements

- Python >= 3.11
- anthropic >= 0.94.0
- python-dotenv >= 1.0.0
