from unittest.mock import MagicMock

import pytest

from simple_agent.config import AgentConfig
from simple_agent.llm_client import LLMClient
from simple_agent.tools import CalculatorTool, SearchTool, ToolRegistry


def make_text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def make_tool_use_block(tool_name: str, tool_input: dict, block_id: str = "tu_123") -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.id = block_id
    block.name = tool_name
    block.input = tool_input
    return block


def make_response(blocks: list) -> MagicMock:
    resp = MagicMock()
    resp.content = blocks
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
