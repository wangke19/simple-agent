import pytest
from pathlib import Path

from simple_agent.scaffold import (
    parse_prd_sections, detect_frameworks, generate_agent_md,
    create_skeleton, run_scaffold, ScaffoldConfig,
)


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
