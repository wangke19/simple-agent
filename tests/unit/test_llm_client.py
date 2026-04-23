from unittest.mock import MagicMock, patch

import pytest

from simple_agent.config import AgentConfig
from simple_agent.exceptions import LLMError
from simple_agent.llm_client import LLMClient


@pytest.fixture
def config():
    return AgentConfig(base_url="https://fake.api", api_key="key", model="test-model")


@pytest.fixture
def mock_anthropic_client(config):
    with patch("simple_agent.llm_client.anthropic.Anthropic") as MockCls:
        mock_client = MockCls.return_value
        yield mock_client, config


def test_call_returns_message(mock_anthropic_client):
    mock_client, config = mock_anthropic_client
    block = MagicMock()
    block.type = "text"
    block.text = "hello"
    mock_client.messages.create.return_value = MagicMock(content=[block])

    client = LLMClient(config)
    response = client.call("system prompt", [{"role": "user", "content": "hi"}])
    assert response.content[0].text == "hello"


def test_call_with_tools(mock_anthropic_client):
    mock_client, config = mock_anthropic_client
    block = MagicMock()
    block.type = "text"
    block.text = "ok"
    mock_client.messages.create.return_value = MagicMock(content=[block])

    client = LLMClient(config)
    tools = [{"name": "test", "description": "desc", "input_schema": {}}]
    client.call("sys", [], tools=tools)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "tools" in call_kwargs


def test_api_connection_error(mock_anthropic_client):
    import anthropic
    mock_client, config = mock_anthropic_client
    mock_client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())

    client = LLMClient(config)
    with pytest.raises(LLMError, match="Connection error"):
        client.call("sys", [])


def test_rate_limit_error(mock_anthropic_client):
    import anthropic
    mock_client, config = mock_anthropic_client
    mock_client.messages.create.side_effect = anthropic.RateLimitError(
        message="rate limited", response=MagicMock(), body=None
    )

    client = LLMClient(config)
    with pytest.raises(LLMError, match="Rate limit"):
        client.call("sys", [])


def test_api_status_error(mock_anthropic_client):
    import anthropic
    mock_client, config = mock_anthropic_client
    mock_client.messages.create.side_effect = anthropic.APIStatusError(
        message="error", response=MagicMock(status_code=500), body=None
    )

    client = LLMClient(config)
    with pytest.raises(LLMError, match="API error"):
        client.call("sys", [])
