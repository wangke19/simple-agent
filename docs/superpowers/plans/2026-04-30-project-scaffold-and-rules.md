# Project Scaffold & Framework Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scaffold phase that creates project skeleton + AGENT.md from PRD, inject framework rules into every task, and enforce rules with real-time guard checks.

**Architecture:** New `scaffold.py` module handles PRD parsing, framework detection, and skeleton creation (no LLM calls). `dev_workflow.py` gains a `rules_block` injection point alongside existing `schema_block` and `contract_block`. `_validate_task_output` gets guard checks for forbidden imports, AGENT.md integrity, and directory structure.

**Tech Stack:** Python 3.10+, pathlib, regex, pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/simple_agent/scaffold.py` | Create | PRD parsing, framework detection, skeleton creation, AGENT.md generation |
| `src/simple_agent/framework_rules/generic.md` | Create | Universal coding pitfalls (error handling, security, logging) |
| `src/simple_agent/framework_rules/pyqt6.md` | Create | PyQt6 known pitfalls (scoped enums, signals, threading) |
| `src/simple_agent/framework_rules/flask.md` | Create | Flask known pitfalls (session, SQL injection, blueprints) |
| `src/simple_agent/framework_rules/fastapi.md` | Create | FastAPI known pitfalls (async, Pydantic v2, dependency injection) |
| `src/simple_agent/agent_md_template.md` | Create | Universal engineering standards template |
| `src/simple_agent/prompts.py` | Modify | Add `rules_injection_template` field |
| `src/simple_agent/messages.py` | Modify | Add scaffold-related messages |
| `src/simple_agent/dev_workflow.py` | Modify | Add `scaffold()`, `rules_block`, guard checks in `_validate_task_output` |
| `build_with_workflow.py` | Modify | Add `--skip-scaffold` flag, call scaffold phase |
| `src/simple_agent/__init__.py` | Modify | Export `ScaffoldConfig`, `ScaffoldResult`, `run_scaffold` |
| `tests/unit/test_scaffold.py` | Create | Unit tests for scaffold module |
| `tests/unit/test_workflow.py` | Modify | Add tests for rules injection and guard checks |

---

### Task 1: Create framework rules knowledge base

**Files:**
- Create: `src/simple_agent/framework_rules/generic.md`
- Create: `src/simple_agent/framework_rules/pyqt6.md`
- Create: `src/simple_agent/framework_rules/flask.md`
- Create: `src/simple_agent/framework_rules/fastapi.md`
- Create: `src/simple_agent/agent_md_template.md`

- [ ] **Step 1: Create `src/simple_agent/framework_rules/generic.md`**

```markdown
# Generic Coding Rules

## Error Handling
- Catch specific exceptions, never bare `except:`
- Display user-friendly error messages, not raw tracebacks
- Log errors with context (what operation, what inputs)

## Security
- No hardcoded secrets, credentials, or API keys
- Validate all user input at system boundaries
- Use parameterized SQL queries — never string interpolation
- Sanitize data before displaying in UI or HTML

## Code Quality
- No placeholder code: no empty `pass`, no `TODO`, no `FIXME`
- Functions should do one thing and have descriptive names
- Avoid magic numbers — use named constants
- Keep imports clean: no unused imports
```

- [ ] **Step 2: Create `src/simple_agent/framework_rules/pyqt6.md`**

```markdown
# PyQt6 Rules

## Enum Syntax (CRITICAL)
PyQt6 uses fully-scoped enum names. The old PyQt5 short form does NOT work:
- WRONG: `QTabWidget.North`, `Qt.AlignCenter`, `QBoxLayout.TopToBottom`
- RIGHT: `QTabWidget.TabPosition.North`, `Qt.AlignmentFlag.AlignCenter`, `QBoxLayout.Direction.TopToBottom`

This applies to ALL Qt enums: `Qt.Orientation`, `Qt.GlobalColor`, `QSizePolicy.Policy`, etc.

## Imports
All imports MUST use `PyQt6`:
```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont
```
Do NOT import from `PyQt5`, `PySide2`, or `PySide6`.

## Signals
Signal connections use the new-style syntax:
```python
button.clicked.connect(self.on_click)  # correct
```
Do NOT use `pyqtSignal` with old-style `SIGNAL()`/`SLOT()` macros.

## Thread Safety
- Never modify UI from a background thread — use signals to communicate
- Use `QThread` with worker objects, not subclassing `QThread.run()`
```

- [ ] **Step 3: Create `src/simple_agent/framework_rules/flask.md`**

```markdown
# Flask Rules

## Session Security
- Always set `SECRET_KEY` from environment variable, never hardcode
- Use `Flask.session` for user sessions, not cookies directly
- Set `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True` in production

## SQL Injection Prevention
- Always use parameterized queries with `?` placeholders
- Never use f-strings or string formatting for SQL queries
- Use SQLAlchemy or raw parameterized queries

## Blueprint Organization
- Use Flask Blueprints to organize routes by feature
- Register blueprints with `url_prefix` in `create_app()` factory
- Keep route handlers thin — business logic in service layer

## Error Handling
- Register error handlers with `@app.errorhandler(404)` etc.
- Return consistent JSON error responses for API endpoints
```

- [ ] **Step 4: Create `src/simple_agent/framework_rules/fastapi.md`**

```markdown
# FastAPI Rules

## Async Pitfalls
- Use `async def` for endpoints that do I/O (database, HTTP calls)
- Use `def` (sync) for CPU-bound endpoints — FastAPI runs them in threadpool
- Never call synchronous blocking code inside `async def` endpoints

## Pydantic v2
- Use `model_validate()` instead of deprecated `parse_obj()`
- Use `model_dump()` instead of deprecated `dict()`
- Config use `model_config = ConfigDict(...)` instead of inner `Config` class

## Dependency Injection
- Use `Depends()` for database sessions, authentication, etc.
- Keep dependency functions small and testable
- Use generator dependencies with `yield` for cleanup (e.g., DB session close)

## Type Hints
- Use Python 3.10+ union syntax: `str | None` instead of `Optional[str]`
- Return models from endpoints for automatic response serialization
```

- [ ] **Step 5: Create `src/simple_agent/agent_md_template.md`**

```markdown
# Engineering Standards

## Required Project Elements
Every generated project MUST have:
- Entry point (main.py / app.py / index.ts / etc.)
- Dependency declaration (requirements.txt / package.json / pyproject.toml)
- AGENT.md (project-specific rules — this file)
- tests/ directory (even if minimal)
- .gitignore

## Quality Gates
- All Python files must pass import check (no syntax or import errors)
- Database projects: schema file is single source of truth for all SQL
- Smoke test must pass (app starts without crash)
- AGENT.md must not be modified or deleted during task execution

## Code Standards
- No placeholder code (TODO, FIXME, pass-only function bodies)
- No hardcoded secrets or credentials
- Error messages must be user-friendly, not raw exceptions
- Use descriptive variable and function names
```

- [ ] **Step 6: Commit**

```bash
git add src/simple_agent/framework_rules/ src/simple_agent/agent_md_template.md
git commit -m "feat: add framework rules knowledge base and engineering standards template"
```

---

### Task 2: Create `scaffold.py` module

**Files:**
- Create: `src/simple_agent/scaffold.py`
- Test: `tests/unit/test_scaffold.py`

- [ ] **Step 1: Write failing tests for PRD parsing**

```python
# tests/unit/test_scaffold.py
import pytest
from pathlib import Path

from simple_agent.scaffold import parse_prd_sections, detect_frameworks


def test_parse_prd_sections_extracts_architecture():
    prd = (
        "# My Project\n\n"
        "## Architecture\n\n"
        "- **UI Framework**: PyQt6 ONLY\n"
        "- **Database**: SQLite\n\n"
        "## Data Model\n\n"
        "### books\n"
        "| Column | Type |\n"
    )
    sections = parse_prd_sections(prd)
    assert "Architecture" in sections
    assert "PyQt6" in sections["Architecture"]
    assert "Data Model" in sections


def test_parse_prd_sections_extracts_conventions():
    prd = (
        "## Conventions\n\n"
        "### Database Access Rules\n"
        "- Use row['column_name']\n\n"
        "### UI Framework Rules\n"
        "- PyQt6 ONLY\n"
    )
    sections = parse_prd_sections(prd)
    assert "Conventions" in sections
    assert "PyQt6" in sections["Conventions"]


def test_parse_prd_sections_empty():
    assert parse_prd_sections("") == {}


def test_parse_prd_sections_no_matching_headings():
    assert parse_prd_sections("Some text\nMore text") == {}


def test_detect_frameworks_pyqt6():
    text = "- **UI Framework**: PyQt6 ONLY (do NOT use PyQt5)"
    frameworks = detect_frameworks(text)
    assert "pyqt6" in frameworks


def test_detect_frameworks_flask():
    text = "- **Backend**: Flask with SQLite"
    frameworks = detect_frameworks(text)
    assert "flask" in frameworks


def test_detect_frameworks_fastapi():
    text = "- **API**: FastAPI + SQLAlchemy"
    frameworks = detect_frameworks(text)
    assert "fastapi" in frameworks


def test_detect_frameworks_none():
    text = "- **Database**: SQLite"
    frameworks = detect_frameworks(text)
    assert frameworks == []


def test_detect_frameworks_multiple():
    text = "Frontend uses React, backend is FastAPI"
    frameworks = detect_frameworks(text)
    assert "react" in frameworks
    assert "fastapi" in frameworks
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_scaffold.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'simple_agent.scaffold'`

- [ ] **Step 3: Implement scaffold.py — PRD parsing and framework detection**

```python
# src/simple_agent/scaffold.py
"""Project scaffold: parse PRD, detect frameworks, create skeleton, generate AGENT.md."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_FRAMEWORK_KEYWORDS: dict[str, list[str]] = {
    "pyqt6": ["pyqt6", "pyqt"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "react": ["react", "reactjs", "react.js"],
}

_RULES_DIR = Path(__file__).parent / "framework_rules"


@dataclass
class ScaffoldConfig:
    """Configuration for scaffold phase."""
    prd_path: str
    output_dir: str
    skip_scaffold: bool = False


@dataclass
class ScaffoldResult:
    """Result of scaffold phase."""
    output_dir: str
    agent_md_path: str
    detected_frameworks: list[str]
    rules_count: int


def parse_prd_sections(prd_text: str) -> dict[str, str]:
    """Extract sections from PRD text by ## headings. Returns {heading: content}."""
    sections: dict[str, str] = {}
    pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(prd_text))
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prd_text)
        content = prd_text[start:end].strip()
        sections[heading] = content
    return sections


def detect_frameworks(text: str) -> list[str]:
    """Detect framework names from text (e.g. Architecture section)."""
    text_lower = text.lower()
    detected = []
    for fw_name, keywords in _FRAMEWORK_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                detected.append(fw_name)
                break
    return detected
```

- [ ] **Step 4: Run parsing tests to verify they pass**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_scaffold.py::test_parse_prd_sections_extracts_architecture tests/unit/test_scaffold.py::test_parse_prd_sections_extracts_conventions tests/unit/test_scaffold.py::test_parse_prd_sections_empty tests/unit/test_scaffold.py::test_parse_prd_sections_no_matching_headings tests/unit/test_scaffold.py::test_detect_frameworks_pyqt6 tests/unit/test_scaffold.py::test_detect_frameworks_flask tests/unit/test_scaffold.py::test_detect_frameworks_fastapi tests/unit/test_scaffold.py::test_detect_frameworks_none tests/unit/test_scaffold.py::test_detect_frameworks_multiple -v`
Expected: all PASS

- [ ] **Step 5: Write failing tests for AGENT.md generation and skeleton creation**

Append to `tests/unit/test_scaffold.py`:

```python
from simple_agent.scaffold import generate_agent_md, create_skeleton, run_scaffold


def test_generate_agent_md_includes_framework_rules(tmp_path):
    prd_sections = {
        "Architecture": "- **UI Framework**: PyQt6 ONLY",
        "Conventions": "### UI Framework Rules\n- PyQt6 ONLY\n",
    }
    content = generate_agent_md(prd_sections, ["pyqt6"])
    assert "PyQt6" in content
    assert "scoped" in content.lower() or "Enum" in content


def test_generate_agent_md_includes_conventions(tmp_path):
    prd_sections = {
        "Architecture": "- **Database**: SQLite",
        "Conventions": "- Use row['column_name']\n- No raw SQL in UI",
    }
    content = generate_agent_md(prd_sections, [])
    assert "row['column_name']" in content


def test_create_skeleton_creates_directories(tmp_path):
    output = tmp_path / "project"
    create_skeleton(str(output), frameworks=["pyqt6"], has_database=True)
    assert (output / "src").is_dir()
    assert (output / "tests").is_dir()
    assert (output / "main.py").exists()
    assert (output / "requirements.txt").exists()
    assert (output / "database_init.sql").exists()
    assert (output / ".gitignore").exists()


def test_create_skeleton_no_database(tmp_path):
    output = tmp_path / "project"
    create_skeleton(str(output), frameworks=[], has_database=False)
    assert not (output / "database_init.sql").exists()


def test_run_scaffold_full(tmp_path):
    prd_path = tmp_path / "design.md"
    prd_path.write_text(
        "# Library System\n\n"
        "## Architecture\n\n"
        "- **UI Framework**: PyQt6 ONLY\n"
        "- **Database**: SQLite\n\n"
        "## Data Model\n\n"
        "### books\n| Column | Type |\n| id | INTEGER |\n\n"
        "## Conventions\n\n"
        "- PyQt6 ONLY across ALL files\n"
    )
    output = tmp_path / "project"
    result = run_scaffold(ScaffoldConfig(str(prd_path), str(output)))
    assert result.detected_frameworks == ["pyqt6"]
    assert (output / "AGENT.md").exists()
    agent_md = (output / "AGENT.md").read_text()
    assert "PyQt6" in agent_md
    assert "scoped" in agent_md.lower() or "Enum" in agent_md
```

- [ ] **Step 6: Run new tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_scaffold.py::test_generate_agent_md_includes_framework_rules tests/unit/test_scaffold.py::test_create_skeleton_creates_directories tests/unit/test_scaffold.py::test_run_scaffold_full -v`
Expected: FAIL — `ImportError: cannot import name 'generate_agent_md'`

- [ ] **Step 7: Implement AGENT.md generation and skeleton creation**

Append to `src/simple_agent/scaffold.py`:

```python
def _load_framework_rules(framework: str) -> str:
    """Load framework-specific rules from knowledge base."""
    rules_file = _RULES_DIR / f"{framework}.md"
    if rules_file.exists():
        return rules_file.read_text(encoding="utf-8").strip()
    return ""


def _load_engineering_standards() -> str:
    """Load the universal engineering standards template."""
    template = Path(__file__).parent / "agent_md_template.md"
    if template.exists():
        return template.read_text(encoding="utf-8").strip()
    return ""


def generate_agent_md(prd_sections: dict[str, str], frameworks: list[str]) -> str:
    """Generate project AGENT.md content from PRD sections and detected frameworks."""
    lines: list[str] = []

    # Section 1: Project-specific rules from PRD
    lines.append("# Project Rules\n")

    # Architecture constraints
    arch = prd_sections.get("Architecture", "")
    if arch:
        lines.append("## Architecture Constraints")
        lines.append(arch)
        lines.append("")

    # Conventions
    conventions = prd_sections.get("Conventions", "") or prd_sections.get("Rules", "")
    if conventions:
        lines.append("## Conventions")
        lines.append(conventions)
        lines.append("")

    # UI Framework Rules (if present as subsection)
    ui_rules = prd_sections.get("UI Framework Rules", "")
    if ui_rules:
        lines.append("## UI Framework Rules")
        lines.append(ui_rules)
        lines.append("")

    # Section 2: Framework-specific pitfalls
    if frameworks:
        lines.append("## Framework Pitfalls (KNOWN ISSUES — avoid these)")
        lines.append("")
        for fw in frameworks:
            rules = _load_framework_rules(fw)
            if rules:
                lines.append(f"### {fw.upper()}")
                lines.append(rules)
                lines.append("")

    # Section 3: Generic rules (always appended)
    generic = _load_framework_rules("generic")
    if generic:
        lines.append("## General Rules")
        lines.append(generic)
        lines.append("")

    return "\n".join(lines)


def create_skeleton(output_dir: str, frameworks: list[str], has_database: bool) -> None:
    """Create project directory skeleton with standard elements."""
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    (base / "src").mkdir(exist_ok=True)
    (base / "tests").mkdir(exist_ok=True)

    # Entry point
    (base / "main.py").write_text("", encoding="utf-8")

    # Requirements — basic dependencies
    deps: list[str] = []
    if "pyqt6" in frameworks:
        deps.append("PyQt6>=6.5.0")
    if "flask" in frameworks:
        deps.append("Flask>=3.0")
    if "fastapi" in frameworks:
        deps.extend(["fastapi>=0.100", "uvicorn>=0.20"])
    (base / "requirements.txt").write_text("\n".join(deps) + "\n", encoding="utf-8")

    # Database schema file
    if has_database:
        (base / "database_init.sql").write_text("", encoding="utf-8")

    # .gitignore
    (base / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n*.pyo\n.env\n*.db\n.reports/\n",
        encoding="utf-8",
    )


def run_scaffold(config: ScaffoldConfig) -> ScaffoldResult:
    """Phase 0: Create project skeleton and AGENT.md from PRD."""
    prd_text = Path(config.prd_path).read_text(encoding="utf-8")
    sections = parse_prd_sections(prd_text)

    # Detect frameworks from Architecture section
    arch_section = sections.get("Architecture", "")
    frameworks = detect_frameworks(arch_section)

    # Check if project has database
    has_database = "Data Model" in sections

    # Create skeleton directories and files
    create_skeleton(config.output_dir, frameworks, has_database)

    # Generate and write project AGENT.md
    agent_md_content = generate_agent_md(sections, frameworks)
    agent_md_path = Path(config.output_dir) / "AGENT.md"
    agent_md_path.write_text(agent_md_content, encoding="utf-8")

    # Count rules (non-empty, non-heading lines)
    rules_count = sum(
        1 for line in agent_md_content.split("\n")
        if line.strip() and not line.startswith("#") and not line.startswith("---")
    )

    return ScaffoldResult(
        output_dir=config.output_dir,
        agent_md_path=str(agent_md_path),
        detected_frameworks=frameworks,
        rules_count=rules_count,
    )
```

- [ ] **Step 8: Run all scaffold tests**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_scaffold.py -v`
Expected: all PASS

- [ ] **Step 9: Export from `__init__.py`**

In `src/simple_agent/__init__.py`, add to imports:

```python
from simple_agent.scaffold import ScaffoldConfig, ScaffoldResult, run_scaffold
```

Add to `__all__`:

```python
"ScaffoldConfig", "ScaffoldResult", "run_scaffold",
```

- [ ] **Step 10: Commit**

```bash
git add src/simple_agent/scaffold.py tests/unit/test_scaffold.py src/simple_agent/__init__.py
git commit -m "feat: add scaffold module with PRD parsing, framework detection, and skeleton creation"
```

---

### Task 3: Add `rules_injection_template` to Prompts and scaffold messages

**Files:**
- Modify: `src/simple_agent/prompts.py:87-100` (add field after `schema_injection_template`)
- Modify: `src/simple_agent/messages.py:28` (add scaffold messages)

- [ ] **Step 1: Add `rules_injection_template` to Prompts dataclass**

In `src/simple_agent/prompts.py`, after the `schema_injection_template` field (line 100), add:

```python
    rules_injection_template: str = (
        "\n\n---\n"
        "## Project Rules (from AGENT.md — STRICTLY follow all rules below)\n"
        "{rules}\n"
        "---\n"
        "## Engineering Standards (non-negotiable)\n"
        "{engineering_standards}\n"
        "---"
    )
```

- [ ] **Step 2: Add Chinese version in `chinese_prompts()`**

In `src/simple_agent/prompts.py`, inside `chinese_prompts()` function (after `schema_injection_template` at line 196), add:

```python
        rules_injection_template=(
            "\n\n---\n"
            "## 项目规则（来自 AGENT.md — 必须严格遵守以下所有规则）\n"
            "{rules}\n"
            "---\n"
            "## 工程标准（不可违反）\n"
            "{engineering_standards}\n"
            "---"
        ),
```

- [ ] **Step 3: Add scaffold messages to Messages dataclass**

In `src/simple_agent/messages.py`, after `workflow_completed` (line 28), add:

```python
    scaffold_complete: str = (
        "Scaffold complete. Framework: {frameworks}. "
        "Rules: {rules_count} items. Project at: {output_dir}"
    )
    guard_agent_md_modified: str = (
        "GUARD: AGENT.md was modified or deleted during execution — this is not allowed"
    )
    guard_forbidden_import: str = (
        "GUARD: Forbidden import detected: {import_name} in {file} "
        "(allowed: {allowed})"
    )
    guard_missing_directory: str = (
        "GUARD: Required directory missing: {directory}"
    )
```

- [ ] **Step 4: Add Chinese versions in `chinese_messages()`**

In `src/simple_agent/messages.py`, inside `chinese_messages()` (after `workflow_completed` at line 48), add:

```python
        scaffold_complete=(
            "项目骨架创建完成。框架: {frameworks}。"
            "规则: {rules_count} 条。项目位于: {output_dir}"
        ),
        guard_agent_md_modified="守卫: AGENT.md 在执行过程中被修改或删除 — 这是不允许的",
        guard_forbidden_import=(
            "守卫: 检测到禁用导入: {import_name} 在 {file} "
            "（允许: {allowed}）"
        ),
        guard_missing_directory="守卫: 缺少必需目录: {directory}",
```

- [ ] **Step 5: Run existing prompt/message tests to verify no breakage**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_prompts.py tests/unit/test_messages.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/simple_agent/prompts.py src/simple_agent/messages.py
git commit -m "feat: add rules_injection_template to Prompts and scaffold guard messages"
```

---

### Task 4: Integrate scaffold into DevWorkflow

**Files:**
- Modify: `src/simple_agent/dev_workflow.py:40-60` (add `scaffold_result` attribute)
- Modify: `src/simple_agent/dev_workflow.py:83-91` (add scaffold call in `run_all`)
- Test: `tests/unit/test_workflow.py` (add scaffold integration tests)

- [ ] **Step 1: Write failing test for scaffold integration**

Append to `tests/unit/test_workflow.py`:

```python
def test_scaffold_adds_rules_block_to_tasks(mock_agent, tmp_path):
    """When scaffold is run, rules_block is injected into task prompts."""
    # Create a minimal PRD file
    prd_path = tmp_path / "design.md"
    prd_path.write_text(
        "# Test\n\n## Architecture\n\n- **UI Framework**: PyQt6 ONLY\n\n"
        "## Data Model\n\n### books\n| id | INTEGER |\n\n"
        "## Conventions\n\n- PyQt6 ONLY\n"
    )
    output_dir = tmp_path / "project"

    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Create main.py\n2. Create ui.py")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="done")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="done")]),
    ]

    from simple_agent.scaffold import ScaffoldConfig, run_scaffold
    scaffold_result = run_scaffold(ScaffoldConfig(str(prd_path), str(output_dir)))

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports", working_dir=str(output_dir))
    wf._scaffold_result = scaffold_result
    wf.plan_task("build a PyQt6 app")
    wf.execute(max_steps_per_task=1)

    # Verify rules_block was injected into LLM calls
    calls = mock_agent._llm.call.call_args_list
    task1_kwargs = calls[1].kwargs
    messages = task1_kwargs.get("messages")
    user_msgs = [m for m in messages if m["role"] == "user"]
    # The task prompt should contain project rules
    assert any("Project Rules" in m.get("content", "") for m in user_msgs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_workflow.py::test_scaffold_adds_rules_block_to_tasks -v`
Expected: FAIL — rules_block not injected yet

- [ ] **Step 3: Add scaffold support to DevWorkflow**

In `src/simple_agent/dev_workflow.py`:

**3a.** Add import at top of file (after line 6):

```python
from simple_agent.scaffold import ScaffoldConfig, ScaffoldResult, run_scaffold
```

**3b.** Add `_scaffold_result` attribute in `__init__` (after line 60):

```python
        self._scaffold_result: ScaffoldResult | None = None
```

**3c.** Add `scaffold()` method after `run_all()` (after line 91):

```python
    def scaffold(self, prd_path: str, output_dir: str, skip: bool = False) -> ScaffoldResult:
        """Phase 0: Create project skeleton and AGENT.md."""
        if skip:
            logger.info("=== Phase 0: Scaffold (skipped) ===")
            # Still load existing AGENT.md if present
            agent_md = Path(output_dir) / "AGENT.md"
            if agent_md.exists():
                self._scaffold_result = ScaffoldResult(
                    output_dir=output_dir,
                    agent_md_path=str(agent_md),
                    detected_frameworks=[],
                    rules_count=0,
                )
            return self._scaffold_result or ScaffoldResult(output_dir, "", [], 0)

        logger.info("=== Phase 0: Scaffold ===")
        config = ScaffoldConfig(prd_path=prd_path, output_dir=output_dir)
        self._scaffold_result = run_scaffold(config)
        logger.info(
            "Scaffold complete: frameworks=%s, rules=%d",
            self._scaffold_result.detected_frameworks,
            self._scaffold_result.rules_count,
        )
        return self._scaffold_result
```

**3d.** Add `_build_rules_block()` helper method (after `_refresh_schema_block`, around line 440):

```python
    def _build_rules_block(self) -> str:
        """Build the rules injection block from project AGENT.md and engineering standards."""
        if not self._scaffold_result:
            return ""

        agent_md_path = Path(self._scaffold_result.agent_md_path)
        if not agent_md_path.exists():
            return ""

        project_rules = agent_md_path.read_text(encoding="utf-8")
        if not project_rules.strip():
            return ""

        # Load universal engineering standards
        from simple_agent.scaffold import _load_engineering_standards
        engineering = _load_engineering_standards()

        return self._prompts.rules_injection_template.format(
            rules=project_rules,
            engineering_standards=engineering,
        )
```

**3e.** Modify `execute()` to include rules_block. Change line 188 from:

```python
            augmented_task = f"{task_item.description}{self._schema_block}{contract_block}"
```

to:

```python
            rules_block = self._build_rules_block()
            augmented_task = f"{task_item.description}{rules_block}{self._schema_block}{contract_block}"
```

**3f.** Modify `resume()` — change line 263 from:

```python
            augmented_task = f"{task_item.description}{self._schema_block}{contract_block}"
```

to:

```python
            rules_block = self._build_rules_block()
            augmented_task = f"{task_item.description}{rules_block}{self._schema_block}{contract_block}"
```

**3g.** Modify `retry_failed()` — change line 356 from:

```python
            augmented_task = f"{read_preamble}{task_item.description}{self._schema_block}{contract_block}{context}"
```

to:

```python
            rules_block = self._build_rules_block()
            augmented_task = f"{read_preamble}{task_item.description}{rules_block}{self._schema_block}{contract_block}{context}"
```

- [ ] **Step 4: Run scaffold integration test**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_workflow.py::test_scaffold_adds_rules_block_to_tasks -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/ -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/simple_agent/dev_workflow.py tests/unit/test_workflow.py
git commit -m "feat: integrate scaffold into DevWorkflow with rules_block injection"
```

---

### Task 5: Add real-time guard checks

**Files:**
- Modify: `src/simple_agent/dev_workflow.py:500-530` (enhance `_validate_task_output`)
- Test: `tests/unit/test_workflow.py` (add guard tests)

- [ ] **Step 1: Write failing tests for guard checks**

Append to `tests/unit/test_workflow.py`:

```python
def test_guard_agent_md_integrity(tmp_path):
    """AGENT.md should not be deleted or emptied."""
    # Create AGENT.md
    agent_md = tmp_path / "AGENT.md"
    agent_md.write_text("# Rules\n- Rule 1\n")

    # Delete it (simulating LLM overwriting)
    agent_md.unlink()

    errors = DevWorkflow._validate_guard_checks(str(tmp_path), agent_md_path=str(agent_md))
    assert any("AGENT.md" in e for e in errors)


def test_guard_forbidden_import_detection(tmp_path):
    """Detect forbidden imports based on AGENT.md content."""
    (tmp_path / "bad.py").write_text("from PyQt5.QtWidgets import QMainWindow\n")
    agent_md = tmp_path / "AGENT.md"
    agent_md.write_text("# Rules\n- PyQt6 ONLY (do NOT use PyQt5)\n")

    errors = DevWorkflow._validate_guard_checks(
        str(tmp_path),
        agent_md_path=str(agent_md),
        allowed_frameworks=["PyQt6"],
        forbidden_frameworks=["PyQt5", "PySide2"],
    )
    assert any("PyQt5" in e for e in errors)


def test_guard_forbidden_import_allows_correct(tmp_path):
    """Correct imports pass the guard."""
    (tmp_path / "good.py").write_text("from PyQt6.QtWidgets import QMainWindow\n")
    agent_md = tmp_path / "AGENT.md"
    agent_md.write_text("# Rules\n- PyQt6 ONLY\n")

    errors = DevWorkflow._validate_guard_checks(
        str(tmp_path),
        agent_md_path=str(agent_md),
        allowed_frameworks=["PyQt6"],
        forbidden_frameworks=["PyQt5", "PySide2"],
    )
    assert not any("PyQt" in e for e in errors)


def test_guard_missing_tests_directory(tmp_path):
    """tests/ directory must exist."""
    agent_md = tmp_path / "AGENT.md"
    agent_md.write_text("# Rules\n")

    errors = DevWorkflow._validate_guard_checks(str(tmp_path), agent_md_path=str(agent_md))
    assert any("tests" in e for e in errors)


def test_guard_passes_when_all_ok(tmp_path):
    """No errors when all checks pass."""
    (tmp_path / "AGENT.md").write_text("# Rules\n- Rule 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "good.py").write_text("from PyQt6.QtWidgets import QMainWindow\n")

    errors = DevWorkflow._validate_guard_checks(
        str(tmp_path),
        agent_md_path=str(tmp_path / "AGENT.md"),
        allowed_frameworks=["PyQt6"],
        forbidden_frameworks=["PyQt5"],
    )
    assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_workflow.py::test_guard_agent_md_integrity tests/unit/test_workflow.py::test_guard_forbidden_import_detection tests/unit/test_workflow.py::test_guard_passes_when_all_ok -v`
Expected: FAIL — `AttributeError: type object 'DevWorkflow' has no attribute '_validate_guard_checks'`

- [ ] **Step 3: Implement guard checks**

In `src/simple_agent/dev_workflow.py`, add a new static method before `_validate_task_output` (before line 500):

```python
    @staticmethod
    def _validate_guard_checks(
        working_dir: str,
        agent_md_path: str = "",
        allowed_frameworks: list[str] | None = None,
        forbidden_frameworks: list[str] | None = None,
    ) -> list[str]:
        """Validate structural integrity and framework rules. Returns error messages."""
        import re as _re
        from pathlib import Path

        errors: list[str] = []
        base = Path(working_dir)

        # Check 1: AGENT.md integrity
        if agent_md_path:
            md = Path(agent_md_path)
            if not md.exists():
                errors.append("GUARD: AGENT.md was deleted during execution — this is not allowed")
            elif md.stat().st_size == 0:
                errors.append("GUARD: AGENT.md was emptied during execution — this is not allowed")

        # Check 2: Forbidden import detection
        if forbidden_frameworks:
            for py_file in sorted(base.rglob("*.py")):
                parts = py_file.relative_to(base).parts
                if any(p.startswith(".") or p == "__pycache__" or p == "site-packages" for p in parts):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue
                for fw in forbidden_frameworks:
                    pattern = rf'(?:^import\s+{fw}|^from\s+{fw})'
                    if _re.search(pattern, content, _re.MULTILINE):
                        rel = py_file.relative_to(base)
                        errors.append(
                            f"GUARD: Forbidden import '{fw}' in {rel} "
                            f"(allowed: {', '.join(allowed_frameworks or [])})"
                        )

        # Check 3: Required directories
        if not (base / "tests").is_dir():
            errors.append("GUARD: Required directory 'tests/' is missing")

        return errors
```

- [ ] **Step 4: Integrate guard checks into `_validate_task_output`**

In `src/simple_agent/dev_workflow.py`, modify `_validate_task_output` to call guard checks. Change the method signature from:

```python
    @staticmethod
    def _validate_task_output(report: TaskReport, working_dir: str) -> list[str]:
```

to:

```python
    @staticmethod
    def _validate_task_output(
        report: TaskReport, working_dir: str,
        agent_md_path: str = "",
        allowed_frameworks: list[str] | None = None,
        forbidden_frameworks: list[str] | None = None,
    ) -> list[str]:
```

And add before the return statement at end of method:

```python
        # Phase 3: Guard checks (AGENT.md integrity, forbidden imports, directory structure)
        guard_errors = DevWorkflow._validate_guard_checks(
            working_dir,
            agent_md_path=agent_md_path,
            allowed_frameworks=allowed_frameworks,
            forbidden_frameworks=forbidden_frameworks,
        )
        errors.extend(guard_errors)
```

- [ ] **Step 5: Pass scaffold info to validation calls in `execute()` and `retry_failed()`**

In `execute()`, change the validation call (around line 205) from:

```python
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir)
```

to:

```python
                guard_kwargs = self._get_guard_kwargs()
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir, **guard_kwargs)
```

In `retry_failed()`, change the validation call (around line 371) from:

```python
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir)
```

to:

```python
                guard_kwargs = self._get_guard_kwargs()
                validation_errors = self._validate_task_output(self._agent.report, self._working_dir, **guard_kwargs)
```

Add helper method after `_build_rules_block()`:

```python
    def _get_guard_kwargs(self) -> dict:
        """Extract guard check parameters from scaffold result."""
        if not self._scaffold_result:
            return {}
        frameworks = self._scaffold_result.detected_frameworks
        allowed = [fw.upper() for fw in frameworks] if frameworks else []
        forbidden_map = {
            "pyqt6": ["PyQt5", "PySide2", "PySide6"],
            "flask": [],
            "fastapi": [],
        }
        forbidden = []
        for fw in frameworks:
            forbidden.extend(forbidden_map.get(fw, []))
        return {
            "agent_md_path": self._scaffold_result.agent_md_path,
            "allowed_frameworks": allowed,
            "forbidden_frameworks": forbidden,
        }
```

- [ ] **Step 6: Run guard tests**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_workflow.py::test_guard_agent_md_integrity tests/unit/test_workflow.py::test_guard_forbidden_import_detection tests/unit/test_workflow.py::test_guard_forbidden_import_allows_correct tests/unit/test_workflow.py::test_guard_missing_tests_directory tests/unit/test_workflow.py::test_guard_passes_when_all_ok -v`
Expected: all PASS

- [ ] **Step 7: Run full test suite**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/ -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add src/simple_agent/dev_workflow.py tests/unit/test_workflow.py
git commit -m "feat: add real-time guard checks for AGENT.md integrity, forbidden imports, and directory structure"
```

---

### Task 6: Integrate scaffold into `build_with_workflow.py`

**Files:**
- Modify: `build_with_workflow.py:172-190` (add `--skip-scaffold` argument)
- Modify: `build_with_workflow.py:293-328` (add scaffold phase, pass scaffold info to workflow)

- [ ] **Step 1: Add `--skip-scaffold` argument**

In `build_with_workflow.py`, after line 189 (`help="List all reports for all tasks"`), add:

```python
    parser.add_argument("--skip-scaffold", action="store_true",
                        help="Skip scaffold phase (for existing projects)")
```

- [ ] **Step 2: Add scaffold phase to full run**

In `build_with_workflow.py`, after `Path(output_dir).mkdir(parents=True, exist_ok=True)` (line 226), add scaffold phase before the agent creation (before line 239):

```python
    # Phase 0: Scaffold — create project skeleton and AGENT.md
    if not args.retry:
        print("=" * 60)
        print("Phase 0: Scaffold")
        print("=" * 60)
        scaffold_result = wf.scaffold(
            prd_path=str(req_path),
            output_dir=output_dir,
            skip=args.skip_scaffold,
        )
        if scaffold_result and scaffold_result.detected_frameworks:
            print(f"  Detected frameworks: {', '.join(scaffold_result.detected_frameworks)}")
            print(f"  Rules: {scaffold_result.rules_count} items")
            print(f"  Project AGENT.md created at: {scaffold_result.agent_md_path}")
        print()
```

Note: the `wf = DevWorkflow(...)` line (line 252) must be moved BEFORE the scaffold call. Restructure so that the agent and workflow are created first, then scaffold is called.

- [ ] **Step 3: Move workflow creation before scaffold**

Move lines 239-252 (agent creation + tool registration + DevWorkflow creation) to right after line 226 (`Path(output_dir).mkdir(...)`). The scaffold call then follows immediately after `wf = DevWorkflow(...)`.

The full run section should look like:

```python
    else:
        # Full run
        print(f"Requirement loaded from: {args.requirement}")
        print(f"Output directory: {output_dir}")
        print(f"{'=' * 60}")
        print(requirement[:200])
        if len(requirement) > 200:
            print(f"... ({len(requirement)} chars total)")
        print()

        # Create agent and workflow
        agent = SimpleAgent(max_failures=3)
        agent._system_prompt = (
            "You are a Python development expert. Use tools to create and modify files, run commands.\n"
            "file_write params: path (filename), content (full code).\n"
            "Complete one task at a time, then give a brief summary."
        )

        agent.register_tool(WriteTool(working_dir=output_dir))
        agent.register_tool(ReadTool(working_dir=output_dir))
        agent.register_tool(EditTool(working_dir=output_dir))
        agent.register_tool(GrepTool(working_dir=output_dir))
        agent.register_tool(BashTool(working_dir=output_dir, timeout=30))

        wf = DevWorkflow(agent, report_dir=f"{output_dir}/.reports", working_dir=output_dir)

        # Phase 0: Scaffold — create project skeleton and AGENT.md
        print("=" * 60)
        print("Phase 0: Scaffold")
        print("=" * 60)
        scaffold_result = wf.scaffold(
            prd_path=str(req_path),
            output_dir=output_dir,
            skip=args.skip_scaffold,
        )
        if scaffold_result and scaffold_result.detected_frameworks:
            print(f"  Detected frameworks: {', '.join(scaffold_result.detected_frameworks)}")
            print(f"  Rules: {scaffold_result.rules_count} items")
        print()

        print("=" * 60)
        print("Phase 1: Planning")
        # ... rest unchanged
```

Remove the duplicate agent creation code (old lines 239-252) since it's now at the top of the else block.

Also for the retry path (inside `if args.retry:` block), move the agent/workflow creation before the scaffold call. Add scaffold with skip=True in retry mode:

```python
    if args.retry:
        # ... (retry path needs agent + wf too)
        agent = SimpleAgent(max_failures=3)
        agent._system_prompt = (
            "You are a Python development expert. Use tools to create and modify files, run commands.\n"
            "file_write params: path (filename), content (full code).\n"
            "Complete one task at a time, then give a brief summary."
        )
        agent.register_tool(WriteTool(working_dir=output_dir))
        agent.register_tool(ReadTool(working_dir=output_dir))
        agent.register_tool(EditTool(working_dir=output_dir))
        agent.register_tool(GrepTool(working_dir=output_dir))
        agent.register_tool(BashTool(working_dir=output_dir, timeout=30))
        wf = DevWorkflow(agent, report_dir=f"{output_dir}/.reports", working_dir=output_dir)

        # Load existing scaffold info (skip creating new one)
        wf.scaffold(prd_path=str(req_path), output_dir=output_dir, skip=True)

        # ... rest of retry logic
```

- [ ] **Step 4: Run a dry check to verify CLI parses correctly**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python build_with_workflow.py --help`
Expected: shows `--skip-scaffold` in help output

- [ ] **Step 5: Commit**

```bash
git add build_with_workflow.py
git commit -m "feat: integrate scaffold phase into build_with_workflow CLI"
```

---

### Task 7: Add scaffold info to report

**Files:**
- Modify: `src/simple_agent/dev_workflow.py:455-483` (enhance `_finalize_report`)

- [ ] **Step 1: Add scaffold section to `_finalize_report()`**

In `dev_workflow.py`, in the `_finalize_report()` method, after the contract section (after line 478 `lines.append(self._contract)`), add:

```python
        if self._scaffold_result:
            lines.append("")
            lines.append("## Scaffold & Rules")
            frameworks = ", ".join(self._scaffold_result.detected_frameworks) or "none detected"
            lines.append(f"- Framework detected: {frameworks}")
            lines.append(f"- Rules file: AGENT.md ({self._scaffold_result.rules_count} rules)")
            lines.append(f"- Guard checks: active ({len(self._scaffold_result.detected_frameworks)} forbidden import patterns)")
```

- [ ] **Step 2: Run existing tests to verify no breakage**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/test_workflow.py -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add src/simple_agent/dev_workflow.py
git commit -m "feat: add scaffold & rules section to workflow report"
```

---

### Task 8: End-to-end verification

**Files:**
- All modified files

- [ ] **Step 1: Run full test suite**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -m pytest tests/unit/ -v`
Expected: all PASS

- [ ] **Step 2: Verify scaffold runs on existing demo PRD**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -c "
from simple_agent.scaffold import ScaffoldConfig, run_scaffold
result = run_scaffold(ScaffoldConfig('demo/books-library-mgmt-design.md', '/tmp/test_scaffold_demo'))
print('Frameworks:', result.detected_frameworks)
print('Rules count:', result.rules_count)
agent_md = open(result.agent_md_path).read()
print('AGENT.md preview:')
print(agent_md[:500])
"`
Expected: frameworks=['pyqt6'], rules_count > 0, AGENT.md contains PyQt6 scoped enum rules

- [ ] **Step 3: Verify forbidden import guard catches PyQt5**

Run: `cd /home/kewang/src/github.com/wangke19/simple-agent && python -c "
from simple_agent.dev_workflow import DevWorkflow
# Write a bad file
import tempfile, pathlib
d = tempfile.mkdtemp()
pathlib.Path(d, 'bad.py').write_text('from PyQt5.QtWidgets import QMainWindow\n')
pathlib.Path(d, 'tests').mkdir()
pathlib.Path(d, 'AGENT.md').write_text('# Rules\n')
errors = DevWorkflow._validate_guard_checks(
    d, agent_md_path=str(pathlib.Path(d, 'AGENT.md')),
    allowed_frameworks=['PyQt6'], forbidden_frameworks=['PyQt5'],
)
print('Errors:', errors)
assert any('PyQt5' in e for e in errors)
print('Guard works correctly!')
"`
Expected: `Guard works correctly!`

- [ ] **Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: any corrections from end-to-end verification"
```
