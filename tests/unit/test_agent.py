import json
from unittest.mock import MagicMock

from simple_agent.tools import CalculatorTool, SearchTool


def test_direct_answer(agent, mock_llm):
    mock_llm.call.return_value = json.dumps({"type": "answer", "content": "你好！"})
    result = agent.run("你好")
    assert result == "你好！"


def test_tool_call_then_answer(agent, mock_llm):
    mock_llm.call.side_effect = [
        json.dumps({"type": "tool", "tool": "search", "input": "北京天气"}),
        json.dumps({"type": "answer", "content": "北京今天晴天，25度"}),
    ]
    result = agent.run("北京天气如何？")
    assert "晴天" in result


def test_max_steps_exceeded(agent, mock_llm):
    mock_llm.call.return_value = json.dumps({"type": "tool", "tool": "search", "input": "x"})
    result = agent.run("test", max_steps=2)
    assert result == "超过最大步数"


def test_tool_registration(agent):
    names = [t.name for t in agent._tools.list_tools()]
    assert "search" in names
    assert "calculate" in names


def test_multi_tool_workflow(agent, mock_llm):
    mock_llm.call.side_effect = [
        json.dumps({"type": "tool", "tool": "search", "input": "北京天气"}),
        json.dumps({"type": "tool", "tool": "calculate", "input": "25 * 9 / 5 + 32"}),
        json.dumps({"type": "answer", "content": "北京25度，华氏77度"}),
    ]
    result = agent.run("北京天气换算华氏")
    assert "77度" in result


def test_messages_history_grows(agent, mock_llm):
    mock_llm.call.side_effect = [
        json.dumps({"type": "tool", "tool": "search", "input": "test"}),
        json.dumps({"type": "answer", "content": "done"}),
    ]
    agent.run("test")
    # Second call should have user + assistant messages
    second_call_msgs = mock_llm.call.call_args_list[1].args[1]
    assert len(second_call_msgs) == 2
    assert second_call_msgs[1]["role"] == "assistant"
    assert "搜索" in second_call_msgs[1]["content"]


def test_json_parse_error_recovery(agent, mock_llm):
    mock_llm.call.side_effect = [
        "this is not json",
        json.dumps({"type": "answer", "content": "recovered"}),
    ]
    result = agent.run("test")
    assert result == "recovered"


def test_unknown_tool_name(agent, mock_llm):
    mock_llm.call.side_effect = [
        json.dumps({"type": "tool", "tool": "nonexistent", "input": "x"}),
        json.dumps({"type": "answer", "content": "sorry"}),
    ]
    result = agent.run("test")
    assert result == "sorry"


def test_unknown_decision_type(agent, mock_llm):
    mock_llm.call.side_effect = [
        json.dumps({"type": "unknown"}),
        json.dumps({"type": "answer", "content": "ok"}),
    ]
    result = agent.run("test")
    assert result == "ok"
