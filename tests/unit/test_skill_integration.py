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
