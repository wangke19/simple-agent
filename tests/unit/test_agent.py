from tests.conftest import make_text_block, make_tool_use_block, make_response


def test_direct_answer(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("Hello!")])
    result = agent.run("hello")
    assert result == "Hello!"


def test_tool_call_then_answer(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "weather"})]),
        make_response([make_text_block("Sunny, 25 degrees")]),
    ]
    result = agent.run("How is the weather?")
    assert "Sunny" in result


def test_max_steps_exceeded(agent, mock_llm):
    mock_llm.call.return_value = make_response([
        make_tool_use_block("search", {"input": "x"})
    ])
    result = agent.run("test", max_steps=2)
    assert result == "Maximum steps exceeded"


def test_tool_registration(agent):
    names = [t.name for t in agent._tools.list_tools()]
    assert "search" in names
    assert "calculate" in names


def test_multi_tool_workflow(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "weather"})]),
        make_response([make_tool_use_block("calculate", {"input": "25 * 9 / 5 + 32"})]),
        make_response([make_text_block("25C is 77F")]),
    ]
    result = agent.run("Convert temperature")
    assert "77" in result


def test_messages_history_grows(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "test"}, "tu_1")]),
        make_response([make_text_block("done")]),
    ]
    agent.run("test")
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
        make_response([make_text_block("Sunny today")]),
        make_response([make_text_block("Yes, sunny as I said")]),
    ]
    agent.run("How is the weather?")
    result = agent.run("What did you say?")

    second_msgs = mock_llm.call.call_args_list[1].kwargs["messages"]
    user_msgs = [m for m in second_msgs if m["role"] == "user"]
    assert len(user_msgs) == 2

    assert "sunny" in result


def test_reset_clears_history(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("ok")])
    agent.run("first")
    assert len(agent._messages_store) > 0

    agent.reset()
    assert len(agent._messages_store) == 0

    agent.run("second")
    first_msgs = mock_llm.call.call_args_list[-1].kwargs["messages"]
    user_msgs = [m for m in first_msgs if m["role"] == "user"]
    assert len(user_msgs) == 1
