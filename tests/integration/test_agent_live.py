import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from simple_agent import SimpleAgent
from simple_agent.tools import CalculatorTool, SearchTool

pytestmark = pytest.mark.integration


@pytest.fixture
def agent():
    a = SimpleAgent()
    a.register_tool(SearchTool())
    a.register_tool(CalculatorTool())
    return a


def test_direct_answer(agent):
    result = agent.run("你好，请介绍一下你自己")
    assert isinstance(result, str)
    assert len(result) > 0


def test_single_tool_call(agent):
    result = agent.run("北京今天天气怎么样？")
    assert isinstance(result, str)
    assert any(kw in result for kw in ["晴天", "25度", "25°C"])


def test_multi_tool_call(agent):
    result = agent.run("北京天气如何？把温度换算成华氏度")
    assert isinstance(result, str)
    assert any(kw in result for kw in ["77", "华氏"])


def test_chinese_conversation(agent):
    result = agent.run("用一句话总结人工智能的意义")
    assert isinstance(result, str)
    assert len(result) > 0
