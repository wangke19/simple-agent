from tests.conftest import make_text_block, make_tool_use_block, make_response


def test_direct_answer(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("你好！")])
    result = agent.run("你好")
    assert result == "你好！"


def test_tool_call_then_answer(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "北京天气"})]),
        make_response([make_text_block("北京今天晴天，25度")]),
    ]
    result = agent.run("北京天气如何？")
    assert "晴天" in result


def test_max_steps_exceeded(agent, mock_llm):
    mock_llm.call.return_value = make_response([
        make_tool_use_block("search", {"input": "x"})
    ])
    result = agent.run("test", max_steps=2)
    assert result == "超过最大步数"


def test_tool_registration(agent):
    names = [t.name for t in agent._tools.list_tools()]
    assert "search" in names
    assert "calculate" in names


def test_multi_tool_workflow(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "北京天气"})]),
        make_response([make_tool_use_block("calculate", {"input": "25 * 9 / 5 + 32"})]),
        make_response([make_text_block("北京25度，华氏77度")]),
    ]
    result = agent.run("北京天气换算华氏")
    assert "77度" in result


def test_messages_history_grows(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "test"}, "tu_1")]),
        make_response([make_text_block("done")]),
    ]
    agent.run("test")
    # Second call should have: user, assistant (tool_use), user (tool_result)
    second_call_msgs = mock_llm.call.call_args_list[1].kwargs["messages"]
    assert len(second_call_msgs) == 3
    assert second_call_msgs[0]["role"] == "user"
    assert second_call_msgs[1]["role"] == "assistant"
    assert second_call_msgs[2]["role"] == "user"


def test_unknown_tool_name(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("nonexistent", {"input": "x"})]),
        make_response([make_text_block("sorry")]),
    ]
    result = agent.run("test")
    assert result == "sorry"


def test_tools_sent_to_api(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("ok")])
    agent.run("test")
    tools = mock_llm.call.call_args.kwargs.get("tools")
    assert tools is not None
    assert len(tools) == 2
    names = {t["name"] for t in tools}
    assert "search" in names
    assert "calculate" in names


def test_multi_turn_conversation(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_text_block("北京晴天")]),
        make_response([make_text_block("是的，北京今天天气不错")]),
    ]
    agent.run("北京天气如何？")
    result = agent.run("刚才你说的是什么？")

    # Second call should see both user messages
    second_msgs = mock_llm.call.call_args_list[1].kwargs["messages"]
    user_msgs = [m for m in second_msgs if m["role"] == "user"]
    assert len(user_msgs) == 2

    assert "天气" in result


def test_reset_clears_history(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("ok")])
    agent.run("first")
    assert len(agent._messages) > 0

    agent.reset()
    assert len(agent._messages) == 0

    agent.run("second")
    # After reset, first call of new conversation should only have 1 user message
    first_msgs = mock_llm.call.call_args_list[-1].kwargs["messages"]
    user_msgs = [m for m in first_msgs if m["role"] == "user"]
    assert len(user_msgs) == 1
