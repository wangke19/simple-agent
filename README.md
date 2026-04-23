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
                       │                     Execute Tool                │
                       │                            │                     │
                       └──── Append result ──────────┘                    │
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

The framework includes a workflow engine that can build complete applications from a requirement file:

```bash
# Create a requirement file
python build_with_workflow.py student_mgmt.md

# Retry failed tasks
python build_with_workflow.py student_mgmt.md --retry
```

The workflow runs 4 phases:
1. **Plan** — LLM generates a development plan
2. **Decompose** — Break into atomic tasks
3. **Define Contracts** — Generate interface specifications between modules
4. **Execute** — Run each task with the contract as shared context

```python
from simple_agent import SimpleAgent, DevWorkflow, Prompts
from simple_agent.tools import WriteTool, ReadTool, EditTool, GrepTool, BashTool

agent = SimpleAgent(max_failures=3)
agent.register_tool(WriteTool(working_dir="my_project"))
agent.register_tool(ReadTool(working_dir="my_project"))
agent.register_tool(EditTool(working_dir="my_project"))
agent.register_tool(GrepTool(working_dir="my_project"))
agent.register_tool(BashTool(working_dir="my_project"))

wf = DevWorkflow(agent, report_dir="my_project/.reports")
wf.run_all("Build a REST API with Flask...")
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
