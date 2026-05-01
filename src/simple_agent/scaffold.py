"""Project scaffold: parse PRD, detect frameworks, create skeleton, generate AGENT.md."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
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
    original_agent_md: str = ""
    required_sections: list[str] = field(default_factory=list)


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


def parse_data_model_columns(data_model_text: str) -> dict[str, list[str]]:
    """Parse Data Model section into {table_name: [column_names]}."""
    tables: dict[str, list[str]] = {}
    if not data_model_text:
        return tables

    table_pattern = re.compile(r'^###\s+(\w+)\s*$', re.MULTILINE)
    matches = list(table_pattern.finditer(data_model_text))

    for i, match in enumerate(matches):
        table_name = match.group(1).lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(data_model_text)
        section = data_model_text[start:end]

        columns = []
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("|--") or line.startswith("| Column") or line.startswith("| column"):
                continue
            if line.startswith("|") and not line.startswith("|>"):
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 2:
                    col_name = cells[1].strip()
                    if col_name and re.match(r'^[a-z_]\w*$', col_name, re.IGNORECASE):
                        columns.append(col_name.lower())

        if columns:
            tables[table_name] = columns

    return tables


def validate_agent_md_sections(
    agent_md_path: str,
    required_sections: list[str],
    original_content: str = "",
) -> list[str]:
    """Validate AGENT.md has all required sections. Returns error list."""
    md = Path(agent_md_path)
    if not md.exists():
        return ["GUARD: AGENT.md was deleted during execution"]
    current = md.read_text(encoding="utf-8")
    if not current.strip():
        return ["GUARD: AGENT.md was emptied during execution"]
    errors = []
    for section in required_sections:
        if f"## {section}" not in current:
            errors.append(f"GUARD: AGENT.md section '{section}' was deleted or corrupted")
    if original_content and len(current) < len(original_content) * 0.5:
        errors.append(
            f"GUARD: AGENT.md shrank from {len(original_content)} to {len(current)} chars"
        )
    return errors


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

    lines.append("# Project Rules\n")

    # Directory structure — standard src-layout architecture
    lines.append("## Directory Structure")
    lines.append("Projects use standard Python src-layout with clear separation of concerns.")
    lines.append("ALL source code goes in `src/`. Do NOT create .py files in project root.")
    lines.append("")
    lines.append("```")
    lines.append("project/")
    lines.append("├── main.py                  # Thin entry point — run from project root")
    lines.append("├── src/                     # ALL source code lives here")
    lines.append("│   ├── __init__.py")
    lines.append("│   ├── app.py               # Application entry — creates and runs app")
    lines.append("│   ├── models.py            # Data models / dataclasses")
    lines.append("│   ├── database/")
    lines.append("│   │   ├── __init__.py")
    lines.append("│   │   ├── db_manager.py    # Database connection and query helpers")
    lines.append("│   │   └── schema.sql       # Single source of truth for DB schema")
    lines.append("│   ├── services/")
    lines.append("│   │   ├── __init__.py")
    lines.append("│   │   └── *_service.py     # One service per domain entity")
    lines.append("│   └── ui/")
    lines.append("│       ├── __init__.py")
    lines.append("│       ├── main_window.py   # Main window — assembles all views")
    lines.append("│       ├── *_tab.py         # Tab / page views")
    lines.append("│       └── *_dialog.py      # Modal dialogs for forms")
    lines.append("├── config/")
    lines.append("│   └── styles.qss           # Stylesheet")
    lines.append("├── tests/")
    lines.append("│   └── smoke_test.py")
    lines.append("├── data/                    # Runtime data (gitignored)")
    lines.append("├── .reports/                # Workflow reports (gitignored)")
    lines.append("├── requirements.txt")
    lines.append("├── AGENT.md")
    lines.append("└── .gitignore")
    lines.append("```")
    lines.append("")
    lines.append("### Import Rules")
    lines.append("All imports use `src.` prefix (running from project root):")
    lines.append("- `from src.ui.main_window import MainWindow`")
    lines.append("- `from src.services.book_service import BookService`")
    lines.append("- `from src.models import Book`")
    lines.append("- `from src.database.db_manager import DatabaseManager`")
    lines.append("- Do NOT use relative imports or sys.path hacks")
    lines.append("- The app is always run from the project root: `python main.py`")
    lines.append("")
    lines.append("### File Placement Rules")
    lines.append("- `main.py` → project root (thin entry point, only 3 lines)")
    lines.append("- `app.py`, `models.py` → `src/`")
    lines.append("- `db_manager.py`, `schema.sql` → `src/database/`")
    lines.append("- `*_service.py` → `src/services/`")
    lines.append("- `*_tab.py`, `*_dialog.py`, `main_window.py` → `src/ui/`")
    lines.append("- `styles.qss` → `config/`")
    lines.append("- Smoke tests → `tests/`")
    lines.append("- Runtime databases (`*.db`) → `data/` (gitignored)")
    lines.append("- Do NOT create .py files in the project root (except main.py)")
    lines.append("")

    arch = prd_sections.get("Architecture", "")
    if arch:
        lines.append("## Architecture Constraints")
        lines.append(arch)
        lines.append("")

    conventions = prd_sections.get("Conventions", "") or prd_sections.get("Rules", "")
    if conventions:
        lines.append("## Conventions")
        lines.append(conventions)
        lines.append("")

    data_model = prd_sections.get("Data Model", "")
    if data_model:
        lines.append("## Data Model")
        lines.append(data_model)
        lines.append("")

    ui_rules = prd_sections.get("UI Framework Rules", "")
    if ui_rules:
        lines.append("## UI Framework Rules")
        lines.append(ui_rules)
        lines.append("")

    if frameworks:
        lines.append("## Framework Pitfalls (KNOWN ISSUES — avoid these)")
        lines.append("")
        for fw in frameworks:
            rules = _load_framework_rules(fw)
            if rules:
                lines.append(f"### {fw.upper()}")
                lines.append(rules)
                lines.append("")

    generic = _load_framework_rules("generic")
    if generic:
        lines.append("## General Rules")
        lines.append(generic)
        lines.append("")

    return "\n".join(lines)


def create_skeleton(output_dir: str, frameworks: list[str], has_database: bool) -> None:
    """Create project directory skeleton with standard src-layout structure."""
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    src = base / "src"
    src.mkdir(exist_ok=True)

    # Source code packages
    for subdir in ("database", "services", "ui"):
        (src / subdir).mkdir(exist_ok=True)

    # __init__.py for all Python packages
    (src / "__init__.py").write_text("", encoding="utf-8")
    for pkg in ("database", "services", "ui"):
        (src / pkg / "__init__.py").write_text("", encoding="utf-8")

    # Entry point at project root (thin wrapper)
    (base / "main.py").write_text(
        "from src.app import main\n\nif __name__ == '__main__':\n    main()\n",
        encoding="utf-8",
    )

    # Actual application code in src/
    (src / "app.py").write_text("", encoding="utf-8")

    # Data model stays at src/ level (shared by all layers)
    if has_database:
        (src / "database" / "schema.sql").write_text("", encoding="utf-8")

    # Non-code directories at project root
    for subdir in ("config", "tests", "data"):
        (base / subdir).mkdir(exist_ok=True)

    deps: list[str] = []
    if "pyqt6" in frameworks:
        deps.append("PyQt6>=6.5.0")
    if "flask" in frameworks:
        deps.append("Flask>=3.0")
    if "fastapi" in frameworks:
        deps.extend(["fastapi>=0.100", "uvicorn>=0.20"])
    (base / "requirements.txt").write_text("\n".join(deps) + "\n", encoding="utf-8")

    (base / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n*.pyo\n.env\ndata/\n*.db\n.reports/\n"
        "test_*.db\n*.log\nSMOKE_TEST_RESULTS.md\n",
        encoding="utf-8",
    )


def run_scaffold(config: ScaffoldConfig) -> ScaffoldResult:
    """Phase 0: Create project skeleton and AGENT.md from PRD."""
    prd_text = Path(config.prd_path).read_text(encoding="utf-8")
    sections = parse_prd_sections(prd_text)

    arch_section = sections.get("Architecture", "")
    frameworks = detect_frameworks(arch_section)

    has_database = "Data Model" in sections

    create_skeleton(config.output_dir, frameworks, has_database)

    agent_md_content = generate_agent_md(sections, frameworks)
    agent_md_path = Path(config.output_dir) / "AGENT.md"
    agent_md_path.write_text(agent_md_content, encoding="utf-8")

    rules_count = sum(
        1 for line in agent_md_content.split("\n")
        if line.strip() and not line.startswith("#") and not line.startswith("---")
    )

    required_sections = [
        s for s in ("Architecture", "Conventions", "Data Model", "UI Framework Rules")
        if s in sections or (s == "Data Model" and has_database)
    ]

    return ScaffoldResult(
        output_dir=config.output_dir,
        agent_md_path=str(agent_md_path),
        detected_frameworks=frameworks,
        rules_count=rules_count,
        original_agent_md=agent_md_content,
        required_sections=required_sections,
    )
