# Skill Call System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add prompt-based skill calling to simple-agent with file-based skill definitions, a UseSkillTool, and two built-in skills (brainstorming, writing-plans).

**Architecture:** Skills are Markdown files with YAML frontmatter auto-discovered from a `skills/` directory. A `SkillRegistry` loads and manages them. A `UseSkillTool` (extending `BaseTool`) lets the LLM activate skills by returning the skill's prompt content as a tool result.

**Tech Stack:** Python 3.11+, pyyaml for frontmatter parsing, pytest for testing

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/simple_agent/skills/__init__.py` | Public exports |
| Create | `src/simple_agent/skills/loader.py` | Parse skill Markdown files |
| Create | `src/simple_agent/skills/registry.py` | Manage loaded skills |
| Create | `src/simple_agent/skills/tool.py` | UseSkillTool (BaseTool subclass) |
| Create | `skills/superpowers/brainstorming.md` | Brainstorming skill prompt |
| Create | `skills/superpowers/writing-plans.md` | Writing-plans skill prompt |
| Create | `tests/unit/test_skill_loader.py` | Loader unit tests |
| Create | `tests/unit/test_skill_registry.py` | Registry unit tests |
| Create | `tests/unit/test_skill_tool.py` | UseSkillTool unit tests |
| Modify | `pyproject.toml` | Add pyyaml dependency |
| Modify | `src/simple_agent/__init__.py` | Export skill classes |

---

### Task 1: Add pyyaml dependency

**Files:**
- Modify: `pyproject.toml:10-13`

- [ ] **Step 1: Add pyyaml to dependencies**

In `pyproject.toml`, add `pyyaml` to the dependencies list:

```toml
dependencies = [
    "anthropic>=0.94.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
]
```

- [ ] **Step 2: Install dependency**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && pip install -e ".[dev]"`

- [ ] **Step 3: Verify import works**

Run: `python -c "import yaml; print(yaml.__version__)"`
Expected: version string printed (e.g., `6.0.2`)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyyaml dependency for skill frontmatter parsing"
```

---

### Task 2: Create Skill dataclass and loader

**Files:**
- Create: `src/simple_agent/skills/__init__.py`
- Create: `src/simple_agent/skills/loader.py`
- Create: `tests/unit/test_skill_loader.py`

- [ ] **Step 1: Write failing tests for loader**

Create `tests/unit/test_skill_loader.py`:

```python
import textwrap
from pathlib import Path

import pytest

from simple_agent.skills.loader import load_skill


@pytest.fixture
def skill_file(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / "test_skill.md"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_load_skill_with_namespace(skill_file):
    content = textwrap.dedent("""\
        ---
        name: brainstorming
        namespace: superpowers
        description: Use before creative work.
        ---

        # Brainstorming

        Ask questions one at a time.
    """)
    skill = load_skill(skill_file(content))
    assert skill.name == "brainstorming"
    assert skill.namespace == "superpowers"
    assert skill.description == "Use before creative work."
    assert "Ask questions one at a time." in skill.content
    assert skill.full_id == "superpowers:brainstorming"


def test_load_skill_without_namespace(skill_file):
    content = textwrap.dedent("""\
        ---
        name: debug
        description: Debug issues step by step.
        ---

        # Debug
        Trace the error.
    """)
    skill = load_skill(skill_file(content))
    assert skill.name == "debug"
    assert skill.namespace == ""
    assert skill.full_id == "debug"


def test_load_skill_missing_name(skill_file):
    content = textwrap.dedent("""\
        ---
        description: No name field.
        ---
        Body here.
    """)
    with pytest.raises(ValueError, match="name"):
        load_skill(skill_file(content))


def test_load_skill_missing_description(skill_file):
    content = textwrap.dedent("""\
        ---
        name: myskill
        ---
        Body here.
    """)
    with pytest.raises(ValueError, match="description"):
        load_skill(skill_file(content))


def test_load_skill_empty_body(skill_file):
    content = textwrap.dedent("""\
        ---
        name: empty
        description: Empty body skill.
        ---
    """)
    skill = load_skill(skill_file(content))
    assert skill.content == ""


def test_load_skill_no_frontmatter(tmp_path):
    p = tmp_path / "no_frontmatter.md"
    p.write_text("Just some text without frontmatter.", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        load_skill(p)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simple_agent.skills'`

- [ ] **Step 3: Create skills package and Skill dataclass**

Create `src/simple_agent/skills/__init__.py`:

```python
from simple_agent.skills.loader import Skill, load_skill
from simple_agent.skills.registry import SkillRegistry
from simple_agent.skills.tool import UseSkillTool

__all__ = ["Skill", "SkillRegistry", "UseSkillTool", "load_skill"]
```

Create `src/simple_agent/skills/loader.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Skill:
    name: str
    namespace: str
    description: str
    content: str
    source_path: Path

    @property
    def full_id(self) -> str:
        if self.namespace:
            return f"{self.namespace}:{self.name}"
        return self.name


def load_skill(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Skill file {path} has no YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Skill file {path} has malformed frontmatter")

    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise ValueError(f"Skill file {path} has invalid frontmatter")

    if "name" not in meta:
        raise ValueError(f"Skill file {path} missing required field: name")
    if "description" not in meta:
        raise ValueError(f"Skill file {path} missing required field: description")

    body = parts[2].strip()

    return Skill(
        name=meta["name"],
        namespace=meta.get("namespace", ""),
        description=meta["description"],
        content=body,
        source_path=path,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_loader.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/simple_agent/skills/__init__.py src/simple_agent/skills/loader.py tests/unit/test_skill_loader.py
git commit -m "feat: add Skill dataclass and loader with YAML frontmatter parsing"
```

---

### Task 3: Create SkillRegistry

**Files:**
- Create: `src/simple_agent/skills/registry.py`
- Create: `tests/unit/test_skill_registry.py`

- [ ] **Step 1: Write failing tests for registry**

Create `tests/unit/test_skill_registry.py`:

```python
import textwrap
from pathlib import Path

import pytest

from simple_agent.skills.loader import Skill
from simple_agent.skills.registry import SkillRegistry


def _write_skill(directory: Path, filename: str, name: str, namespace: str = "", description: str = "A skill.") -> Path:
    p = directory / filename
    frontmatter = f"name: {name}\n"
    if namespace:
        frontmatter += f"namespace: {namespace}\n"
    frontmatter += f"description: {description}\n"
    p.write_text(f"---\n{frontmatter}---\n\n# {name}\nBody of {name}.", encoding="utf-8")
    return p


@pytest.fixture
def skills_dir(tmp_path):
    return tmp_path / "skills"


def test_load_skills_from_directory(skills_dir):
    sub = skills_dir / "superpowers"
    sub.mkdir(parents=True)
    _write_skill(sub, "brainstorming.md", "brainstorming", "superpowers")
    _write_skill(sub, "writing-plans.md", "writing-plans", "superpowers")

    reg = SkillRegistry(skills_dir)
    assert len(reg.list_skills()) == 2


def test_get_by_full_id(skills_dir):
    sub = skills_dir / "superpowers"
    sub.mkdir(parents=True)
    _write_skill(sub, "brainstorming.md", "brainstorming", "superpowers")

    reg = SkillRegistry(skills_dir)
    skill = reg.get("superpowers:brainstorming")
    assert skill.name == "brainstorming"


def test_get_by_short_name(skills_dir):
    sub = skills_dir / "superpowers"
    sub.mkdir(parents=True)
    _write_skill(sub, "brainstorming.md", "brainstorming", "superpowers")

    reg = SkillRegistry(skills_dir)
    skill = reg.get("brainstorming")
    assert skill.name == "brainstorming"


def test_get_unknown_skill_raises(skills_dir):
    skills_dir.mkdir(parents=True)
    reg = SkillRegistry(skills_dir)
    with pytest.raises(KeyError, match="nonexistent"):
        reg.get("nonexistent")


def test_empty_directory(skills_dir):
    skills_dir.mkdir(parents=True)
    reg = SkillRegistry(skills_dir)
    assert len(reg.list_skills()) == 0


def test_skill_descriptions_format(skills_dir):
    sub = skills_dir / "superpowers"
    sub.mkdir(parents=True)
    _write_skill(sub, "brainstorming.md", "brainstorming", "superpowers", "Explore ideas before coding.")
    _write_skill(sub, "writing-plans.md", "writing-plans", "superpowers", "Write step-by-step plans.")

    reg = SkillRegistry(skills_dir)
    desc = reg.skill_descriptions()
    assert "superpowers:brainstorming" in desc
    assert "Explore ideas before coding." in desc
    assert "superpowers:writing-plans" in desc


def test_nonexistent_skills_dir(tmp_path):
    reg = SkillRegistry(tmp_path / "nonexistent")
    assert len(reg.list_skills()) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_registry.py -v`
Expected: FAIL with `ImportError` (registry module does not exist yet)

- [ ] **Step 3: Implement SkillRegistry**

Create `src/simple_agent/skills/registry.py`:

```python
from __future__ import annotations

import logging
from pathlib import Path

from simple_agent.skills.loader import Skill, load_skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self._skills: dict[str, Skill] = {}
        self._load_all(skills_dir)

    def _load_all(self, skills_dir: Path) -> None:
        if not skills_dir.is_dir():
            logger.debug("Skills directory not found: %s", skills_dir)
            return

        for path in skills_dir.rglob("*.md"):
            try:
                skill = load_skill(path)
                self._skills[skill.full_id] = skill
                logger.debug("Loaded skill: %s", skill.full_id)
            except Exception as e:
                logger.warning("Failed to load skill %s: %s", path, e)

    def get(self, skill_id: str) -> Skill:
        if skill_id in self._skills:
            return self._skills[skill_id]
        for skill in self._skills.values():
            if skill.name == skill_id:
                return skill
        raise KeyError(f"Unknown skill: '{skill_id}'")

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def skill_descriptions(self) -> str:
        if not self._skills:
            return "No skills available."
        lines = []
        for skill in self._skills.values():
            lines.append(f"- {skill.full_id} - {skill.description}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_registry.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/simple_agent/skills/registry.py tests/unit/test_skill_registry.py
git commit -m "feat: add SkillRegistry with directory scanning and lookup"
```

---

### Task 4: Create UseSkillTool

**Files:**
- Create: `src/simple_agent/skills/tool.py`
- Create: `tests/unit/test_skill_tool.py`

- [ ] **Step 1: Write failing tests for UseSkillTool**

Create `tests/unit/test_skill_tool.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from simple_agent.skills.loader import Skill
from simple_agent.skills.registry import SkillRegistry
from simple_agent.skills.tool import UseSkillTool


@pytest.fixture
def mock_registry():
    reg = MagicMock(spec=SkillRegistry)
    reg.skill_descriptions.return_value = "- test:skill - A test skill."
    reg.get.return_value = Skill(
        name="skill",
        namespace="test",
        description="A test skill.",
        content="# Test Skill\nDo the thing.",
        source_path=Path("skills/test/skill.md"),
    )
    return reg


@pytest.fixture
def tool(mock_registry):
    return UseSkillTool(skill_registry=mock_registry)


def test_tool_name(tool):
    assert tool.name == "use_skill"


def test_tool_description_includes_skills(tool):
    desc = tool.description
    assert "test:skill" in desc
    assert "A test skill." in desc


def test_execute_returns_skill_content(tool):
    result = tool.execute(skill_name="test:skill")
    assert "# Test Skill" in result
    assert "Do the thing." in result


def test_execute_with_args(tool):
    result = tool.execute(skill_name="test:skill", args="build a chat app")
    assert "# Test Skill" in result
    assert "build a chat app" in result


def test_execute_unknown_skill(tool, mock_registry):
    mock_registry.get.side_effect = KeyError("Unknown skill: 'missing'")
    result = tool.execute(skill_name="missing")
    assert "Error" in result
    assert "missing" in result


def test_parameters_schema(tool):
    params = tool.parameters
    assert "skill_name" in params["properties"]
    assert "args" in params["properties"]
    assert params["required"] == ["skill_name"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_tool.py -v`
Expected: FAIL with `ImportError` (tool module does not exist yet)

- [ ] **Step 3: Implement UseSkillTool**

Create `src/simple_agent/skills/tool.py`:

```python
from __future__ import annotations

from typing import Any

from simple_agent.tools.base import BaseTool
from simple_agent.skills.registry import SkillRegistry


class UseSkillTool(BaseTool):
    name = "use_skill"

    def __init__(self, skill_registry: SkillRegistry, description: str | None = None) -> None:
        super().__init__(description=description)
        self._registry = skill_registry

    @property
    def _default_description(self) -> str:
        header = "Activate a named skill to inject specialized instructions into the conversation.\n\nAvailable skills:"
        return f"{header}\n{self._registry.skill_descriptions()}"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Full skill ID (e.g., 'superpowers:brainstorming') or short name",
                },
                "args": {
                    "type": "string",
                    "description": "Optional arguments to pass to the skill",
                },
            },
            "required": ["skill_name"],
        }

    def execute(self, **kwargs: Any) -> str:
        skill_name = kwargs.get("skill_name", "")
        args = kwargs.get("args", "")

        try:
            skill = self._registry.get(skill_name)
        except KeyError as e:
            return f"Error: {e}"

        result = skill.content
        if args:
            result += f"\n\n---\n## User context\n{args}"
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_tool.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/simple_agent/skills/tool.py tests/unit/test_skill_tool.py
git commit -m "feat: add UseSkillTool with dynamic skill descriptions"
```

---

### Task 5: Create built-in skill files

**Files:**
- Create: `skills/superpowers/brainstorming.md`
- Create: `skills/superpowers/writing-plans.md`

- [ ] **Step 1: Create brainstorming skill**

Create `skills/superpowers/brainstorming.md`:

```markdown
---
name: brainstorming
namespace: superpowers
description: >
  Use before any creative work — creating features, building components,
  adding functionality, or modifying behavior. Explores user intent,
  requirements, and design before implementation.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

## Process

1. **Explore project context** — check files, docs, recent commits to understand the current state
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria. Prefer multiple choice when possible
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to complexity, get user approval after each section
5. **Write design doc** — save the approved design and commit it

## Rules

- Never implement until the design is approved
- One question per message — don't overwhelm
- YAGNI ruthlessly — remove unnecessary features from designs
- Always propose alternatives before settling on one approach
- Be ready to go back and clarify when something doesn't make sense

## Design Sections

When presenting the final design, cover:
- Architecture and components
- Data flow
- Error handling
- Testing strategy

Scale each section to its complexity: a few sentences if straightforward, more detail if nuanced.
```

- [ ] **Step 2: Create writing-plans skill**

Create `skills/superpowers/writing-plans.md`:

```markdown
---
name: writing-plans
namespace: superpowers
description: >
  Use when you have a spec or requirements for a multi-step task and need to
  create a detailed, step-by-step implementation plan before writing code.
---

# Writing Implementation Plans

Create comprehensive implementation plans from an approved design spec. Plans are bite-sized, testable tasks that an engineer can execute sequentially.

## Process

1. **Read the spec** — understand the full scope and all requirements
2. **Map file structure** — list every file that will be created or modified, with its responsibility
3. **Break into tasks** — each task is one focused change (a dataclass, a function, a test file)
4. **Order tasks** — each task depends only on tasks before it

## Task Granularity

Each step in a task is ONE action:
- Write the failing test
- Run it to see it fail
- Write minimal implementation
- Run tests to see them pass
- Commit

## Rules

- Every step must contain actual code — no placeholders, no "TBD", no "implement similar to X"
- Exact file paths always
- Complete code in every step
- TDD: test first, then implement
- Frequent small commits
- DRY and YAGNI
```

- [ ] **Step 3: Verify skills load correctly**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -c "
from pathlib import Path
from simple_agent.skills import SkillRegistry
reg = SkillRegistry(Path('skills'))
for s in reg.list_skills():
    print(f'{s.full_id}: {s.description[:60]}...')
"`
Expected: Prints both `superpowers:brainstorming` and `superpowers:writing-plans`

- [ ] **Step 4: Commit**

```bash
git add skills/
git commit -m "feat: add brainstorming and writing-plans built-in skills"
```

---

### Task 6: Export skill classes from package

**Files:**
- Modify: `src/simple_agent/__init__.py`

- [ ] **Step 1: Read current exports**

Read: `src/simple_agent/__init__.py`

- [ ] **Step 2: Add skill exports**

Add these lines to the existing imports and `__all__` in `src/simple_agent/__init__.py`:

```python
from simple_agent.skills import Skill, SkillRegistry, UseSkillTool, load_skill
```

And add to `__all__`:
```python
    "Skill",
    "SkillRegistry",
    "UseSkillTool",
    "load_skill",
```

- [ ] **Step 3: Verify imports work**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -c "from simple_agent import SkillRegistry, UseSkillTool; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Run all tests**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/ -v`
Expected: All existing + new tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/simple_agent/__init__.py
git commit -m "feat: export skill classes from simple_agent package"
```

---

### Task 7: Integration test with agent

**Files:**
- Create: `tests/unit/test_skill_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/unit/test_skill_integration.py`:

```python
"""Integration test: UseSkillTool works within the agent's tool loop."""
from pathlib import Path
from unittest.mock import MagicMock

from simple_agent.agent import SimpleAgent
from simple_agent.config import AgentConfig
from simple_agent.llm_client import LLMClient
from simple_agent.skills import SkillRegistry, UseSkillTool
from simple_agent.tools.registry import ToolRegistry


def _setup_agent_with_skill(tmp_path):
    skills_dir = tmp_path / "skills"
    sub = skills_dir / "test"
    sub.mkdir(parents=True)
    (sub / "echo.md").write_text(
        "---\nname: echo\nnamespace: test\ndescription: Echo skill.\n---\n\n# Echo\nYou are in echo mode.",
        encoding="utf-8",
    )

    config = AgentConfig(base_url="https://fake", api_key="k", model="m")
    mock_llm = MagicMock(spec=LLMClient)
    registry = ToolRegistry()
    skill_reg = SkillRegistry(skills_dir)
    registry.register(UseSkillTool(skill_registry=skill_reg))

    agent = SimpleAgent(config=config, llm_client=mock_llm, tool_registry=registry)
    return agent, mock_llm


def test_agent_calls_use_skill_tool(tmp_path):
    agent, mock_llm = _setup_agent_with_skill(tmp_path)

    from tests.conftest import make_text_block, make_tool_use_block, make_response

    skill_call = make_tool_use_block("use_skill", {"skill_name": "test:echo"}, "tu_skill")
    skill_result_text = make_text_block("I am now in echo mode. Let me help you.")
    first_call = make_response([skill_call])
    second_call = make_response([skill_result_text])

    mock_llm.call.side_effect = [first_call, second_call]

    result = agent.run("activate the echo skill")
    assert "echo mode" in result


def test_use_skill_in_api_format(tmp_path):
    """Verify UseSkillTool produces valid Anthropic API format."""
    skills_dir = tmp_path / "skills"
    sub = skills_dir / "test"
    sub.mkdir(parents=True)
    (sub / "demo.md").write_text(
        "---\nname: demo\ndescription: A demo.\n---\n\n# Demo\nDo stuff.",
        encoding="utf-8",
    )

    reg = ToolRegistry()
    skill_reg = SkillRegistry(skills_dir)
    tool = UseSkillTool(skill_registry=skill_reg)
    reg.register(tool)

    api_tools = reg.to_api_format()
    skill_tool = next(t for t in api_tools if t["name"] == "use_skill")
    assert "demo" in skill_tool["description"]
    assert "skill_name" in skill_tool["input_schema"]["properties"]
```

- [ ] **Step 2: Run integration tests**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_skill_integration.py -v`
Expected: All 2 tests PASS

- [ ] **Step 3: Run full test suite**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/ -v`
Expected: All tests PASS (existing + new skill tests)

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_skill_integration.py
git commit -m "test: add integration tests for skill tool with agent"
```
