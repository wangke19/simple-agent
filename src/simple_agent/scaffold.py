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
    """Create project directory skeleton with standard elements."""
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    (base / "src").mkdir(exist_ok=True)
    (base / "tests").mkdir(exist_ok=True)

    (base / "main.py").write_text("", encoding="utf-8")

    deps: list[str] = []
    if "pyqt6" in frameworks:
        deps.append("PyQt6>=6.5.0")
    if "flask" in frameworks:
        deps.append("Flask>=3.0")
    if "fastapi" in frameworks:
        deps.extend(["fastapi>=0.100", "uvicorn>=0.20"])
    (base / "requirements.txt").write_text("\n".join(deps) + "\n", encoding="utf-8")

    if has_database:
        (base / "database_init.sql").write_text("", encoding="utf-8")

    (base / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n*.pyo\n.env\n*.db\n.reports/\n",
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

    return ScaffoldResult(
        output_dir=config.output_dir,
        agent_md_path=str(agent_md_path),
        detected_frameworks=frameworks,
        rules_count=rules_count,
    )
