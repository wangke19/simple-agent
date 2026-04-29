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
