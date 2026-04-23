from tests.conftest import make_text_block, make_tool_use_block, make_response


def test_agent_creates_report(agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("done")])
    agent.run("test task")
    assert agent.report is not None
    assert agent.report.task == "test task"
    assert agent.report.status == "completed"


def test_failure_count_resets_on_success(agent, mock_llm):
    """Success after failure should reset the failure counter."""
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("nonexistent_tool", {"input": "x"})]),
        make_response([make_text_block("recovered")]),
    ]
    agent._max_failures = 3
    result = agent.run("test")
    assert result == "recovered"
    assert agent._failure_count == 0


def test_paused_on_max_failures(agent, mock_llm):
    """Agent should pause when failures exceed max_failures."""
    mock_llm.call.return_value = make_response([
        make_tool_use_block("nonexistent_tool", {"input": "x"})
    ])
    agent._max_failures = 2
    result = agent.run("test", max_steps=10)
    assert "paused" in result.lower()
    assert agent.report.status == "paused"
    assert agent.report.failed_steps >= 2


def test_resume_after_pause(agent, mock_llm):
    """Agent can resume after being paused."""
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("nonexistent_tool", {"input": "x"})]),
        make_response([make_tool_use_block("nonexistent_tool", {"input": "x"})]),
        # After resume:
        make_response([make_text_block("all good now")]),
    ]
    agent._max_failures = 2
    result1 = agent.run("test task", max_steps=5)
    assert "paused" in result1.lower()

    result2 = agent.resume("try a different approach")
    assert result2 == "all good now"
    assert agent.report.status == "completed"


def test_resume_without_pause_raises(agent):
    import pytest
    with pytest.raises(RuntimeError, match="No paused task"):
        agent.resume("guidance")


def test_report_has_steps(agent, mock_llm):
    mock_llm.call.side_effect = [
        make_response([make_tool_use_block("search", {"input": "weather"})]),
        make_response([make_text_block("sunny")]),
    ]
    agent.run("weather")
    assert agent.report.total_steps == 2
    assert agent.report.steps[0].tool_name == "search"
    assert agent.report.steps[1].action == "answer"


def test_report_saves(tmp_path, agent, mock_llm):
    mock_llm.call.return_value = make_response([make_text_block("done")])
    agent.run("test")
    path = tmp_path / "report.md"
    agent.report.save(path)
    content = path.read_text()
    assert "test" in content
    assert "Checklist" in content
