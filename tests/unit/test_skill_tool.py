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
