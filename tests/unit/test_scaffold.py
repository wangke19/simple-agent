import pytest
from pathlib import Path

from simple_agent.scaffold import (
    parse_prd_sections, detect_frameworks, generate_agent_md,
    create_skeleton, run_scaffold, ScaffoldConfig,
    parse_data_model_columns,
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
    assert (output / "tests").is_dir()
    assert (output / "main.py").exists()
    assert (output / "requirements.txt").exists()
    assert (output / "database_init.sql").exists()
    assert (output / ".gitignore").exists()
    assert not (output / "src").exists()


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


def test_parse_data_model_columns_basic():
    text = (
        "### books\n"
        "| Column | Type | Constraints |\n"
        "|--------|------|-------------|\n"
        "| id | INTEGER | PRIMARY KEY |\n"
        "| title | TEXT | NOT NULL |\n"
        "| isbn | TEXT | |\n"
    )
    result = parse_data_model_columns(text)
    assert "books" in result
    assert result["books"] == ["id", "title", "isbn"]


def test_parse_data_model_columns_multiple_tables():
    text = (
        "### books\n"
        "| Column | Type |\n"
        "|--------|------|\n"
        "| id | INTEGER |\n"
        "| title | TEXT |\n\n"
        "### members\n"
        "| Column | Type |\n"
        "|--------|------|\n"
        "| id | INTEGER |\n"
        "| email | TEXT |\n"
    )
    result = parse_data_model_columns(text)
    assert "books" in result
    assert "members" in result
    assert result["books"] == ["id", "title"]
    assert result["members"] == ["id", "email"]


def test_parse_data_model_columns_empty():
    assert parse_data_model_columns("") == {}
    assert parse_data_model_columns("no tables here") == {}


def test_generate_agent_md_includes_data_model():
    prd_sections = {
        "Architecture": "- **Database**: SQLite",
        "Data Model": "### books\n| Column | Type |\n| id | INTEGER |\n",
    }
    content = generate_agent_md(prd_sections, [])
    assert "## Data Model" in content
    assert "books" in content


def test_generate_agent_md_without_data_model():
    prd_sections = {
        "Architecture": "- **Database**: SQLite",
    }
    content = generate_agent_md(prd_sections, [])
    assert "## Data Model" not in content
