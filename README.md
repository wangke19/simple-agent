# Simple Agent

A minimal AI agent framework demonstrating the core observe-decide-act loop with tool-calling capabilities.

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
                        └────── Append result ────────┘                    │
                                                                         ▼
                                                                    Return Result
```

The agent runs a bounded decision loop. At each step, the LLM either calls a registered tool or returns a final answer. Tool results are appended to the conversation history, and the LLM is called again until it produces an answer or the step limit is reached.

## Quick Start

```bash
# Install
pip install -e .

# Configure (copy and edit)
cp .env.example .env

# Run demo
python main.py
```

## Configuration

Set environment variables in `.env`:

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_BASE_URL` | API base URL | `https://api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | API key (required) | — |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Model name | `claude-sonnet-4-20250514` |
| `AGENT_MAX_STEPS` | Max decision loop steps | `5` |
| `AGENT_LOG_LEVEL` | Logging level | `INFO` |

## Usage

```python
from dotenv import load_dotenv
from simple_agent import SimpleAgent
from simple_agent.tools import SearchTool, CalculatorTool

load_dotenv()

agent = SimpleAgent()
agent.register_tool(SearchTool())
agent.register_tool(CalculatorTool())

result = agent.run("北京今天天气怎么样？")
print(result)
```

## Creating Custom Tools

Subclass `BaseTool`:

```python
from simple_agent.tools.base import BaseTool

class TranslateTool(BaseTool):
    name = "translate"
    description = "翻译文本"

    def execute(self, input: str) -> str:
        # your implementation
        return translated_text

agent.register_tool(TranslateTool())
```

## Project Structure

```
src/simple_agent/
├── agent.py          # Decision loop orchestrator
├── config.py         # AgentConfig dataclass, reads from env
├── llm_client.py     # Anthropic SDK wrapper with error handling
├── exceptions.py     # AgentError, LLMError, ToolError, ResponseParseError
├── prompts.py        # System prompt template
└── tools/
    ├── base.py       # BaseTool ABC (name, description, execute)
    ├── registry.py   # ToolRegistry (register, get, format_descriptions)
    ├── search.py     # SearchTool (mock)
    └── calculator.py # CalculatorTool
```

## Testing

```bash
# Unit tests (mocked LLM)
python -m pytest tests/unit/ -v

# Integration tests (real API)
python -m pytest tests/integration/ -v

# All tests
python -m pytest tests/ -v
```

## Requirements

- Python >= 3.11
- anthropic >= 0.94.0
- python-dotenv >= 1.0.0
