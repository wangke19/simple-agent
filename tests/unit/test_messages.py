from simple_agent.messages import Messages, chinese_messages


def test_default_messages_are_english():
    m = Messages()
    assert "Consecutive LLM" in m.llm_failures
    assert "Maximum steps" in m.max_steps_exceeded
    assert "Task paused" in m.task_paused
    assert "Tool error" in m.tool_error
    assert "No paused task" in m.no_paused_task


def test_default_messages_non_empty():
    m = Messages()
    for field in [
        "llm_failures", "tool_failures", "max_steps_exceeded",
        "llm_failures_resumed", "tool_failures_resumed", "max_steps_resumed",
        "task_paused", "tool_error", "no_paused_task",
        "workflow_paused", "workflow_completed",
    ]:
        assert len(getattr(m, field)) > 0


def test_chinese_messages():
    m = chinese_messages()
    assert "LLM调用" in m.llm_failures
    assert "超过最大步数" in m.max_steps_exceeded


def test_template_formatting():
    m = Messages()
    result = m.task_paused.format(reason="test failure")
    assert "test failure" in result

    result = m.workflow_completed.format(total=5, passed=4)
    assert "5" in result
    assert "4" in result
