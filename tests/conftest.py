import json
from unittest.mock import MagicMock

import pytest

from simple_agent.config import AgentConfig
from simple_agent.llm_client import LLMClient
from simple_agent.tools import CalculatorTool, SearchTool, ToolRegistry


def make_llm_response(content: str) -> MagicMock:
    block = MagicMock()
    block.text = content
    resp = MagicMock()
    resp.content = [block]
    return resp


@pytest.fixture
def config():
    return AgentConfig(
        base_url="https://fake.api",
        api_key="test-key",
        model="test-model",
    )


@pytest.fixture
def mock_llm(config):
    client = MagicMock(spec=LLMClient)
    client._config = config
    return client


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(SearchTool())
    r.register(CalculatorTool())
    return r


@pytest.fixture
def agent(mock_llm, config, registry):
    from simple_agent.agent import SimpleAgent
    return SimpleAgent(config=config, llm_client=mock_llm, tool_registry=registry)
