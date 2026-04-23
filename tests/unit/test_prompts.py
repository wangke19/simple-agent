from simple_agent.prompts import build_system_prompt, TOOL_CALL_FORMAT, ANSWER_FORMAT


def test_build_system_prompt_contains_tools():
    prompt = build_system_prompt("search: 搜索\ncalculate: 计算")
    assert "search" in prompt
    assert "calculate" in prompt


def test_build_system_prompt_contains_json_format():
    prompt = build_system_prompt("test: desc")
    assert '"type":"tool"' in prompt
    assert '"type":"answer"' in prompt


def test_format_constants():
    assert '"tool"' in TOOL_CALL_FORMAT
    assert '"answer"' in ANSWER_FORMAT
