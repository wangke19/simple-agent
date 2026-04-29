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
