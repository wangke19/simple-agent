import pytest
from unittest.mock import MagicMock

from simple_agent.compactor import estimate_tokens, compact_messages


def test_estimate_tokens_string_messages():
    messages = [
        {"role": "user", "content": "a" * 100},
        {"role": "assistant", "content": "b" * 200},
    ]
    tokens = estimate_tokens(messages)
    assert tokens == 75  # (100 + 200) // 4


def test_estimate_tokens_list_content():
    messages = [
        {"role": "assistant", "content": [
            {"type": "text", "text": "hello"},
            {"type": "tool_use", "name": "search", "input": {"q": "test"}},
        ]},
    ]
    tokens = estimate_tokens(messages)
    assert tokens > 0


def test_no_compaction_below_threshold():
    messages = [
        {"role": "user", "content": "short"},
        {"role": "assistant", "content": "reply"},
    ]
    mock_llm = MagicMock()
    result = compact_messages(
        messages, keep_recent=1, llm=mock_llm,
        max_context_tokens=100000, compact_threshold=0.8,
    )
    assert result is messages  # unchanged
    mock_llm.call.assert_not_called()


def test_compaction_triggers_above_threshold():
    # Create messages that exceed threshold
    messages = []
    for i in range(20):
        messages.append({"role": "user", "content": "x" * 1000})
        messages.append({"role": "assistant", "content": "y" * 1000})

    # Low threshold to trigger compaction
    mock_llm = MagicMock()
    summary_block = MagicMock()
    summary_block.text = "用户问了20个问题，助手的回复都很短"
    mock_resp = MagicMock()
    mock_resp.content = [summary_block]
    mock_llm.call.return_value = mock_resp

    result = compact_messages(
        messages, keep_recent=2, llm=mock_llm,
        max_context_tokens=1000, compact_threshold=0.5,
    )

    # Should have: 1 summary + 2 recent = 3
    assert len(result) == 3
    assert "摘要" in result[0]["content"]
    assert result[1] is messages[-2]
    assert result[2] is messages[-1]
    mock_llm.call.assert_called_once()


def test_compaction_keeps_all_if_too_few_messages():
    messages = [
        {"role": "user", "content": "x" * 10000},
    ]
    mock_llm = MagicMock()
    # Even though tokens exceed threshold, only 1 message and keep_recent=4
    result = compact_messages(
        messages, keep_recent=4, llm=mock_llm,
        max_context_tokens=100, compact_threshold=0.5,
    )
    assert result is messages
    mock_llm.call.assert_not_called()


def test_compaction_summary_failure_falls_back():
    messages = []
    for i in range(10):
        messages.append({"role": "user", "content": "x" * 1000})
        messages.append({"role": "assistant", "content": "y" * 1000})

    mock_llm = MagicMock()
    mock_llm.call.side_effect = Exception("API error")

    result = compact_messages(
        messages, keep_recent=2, llm=mock_llm,
        max_context_tokens=1000, compact_threshold=0.5,
    )

    # Should still compact with fallback summary
    assert len(result) == 3
    assert "摘要生成失败" in result[0]["content"]
