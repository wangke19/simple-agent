import pytest
from unittest.mock import MagicMock

from simple_agent.config import AgentConfig
from simple_agent.dev_workflow import DevWorkflow
from simple_agent import SimpleAgent
from tests.conftest import make_text_block


@pytest.fixture
def mock_agent():
    config = AgentConfig(base_url="https://fake", api_key="key", model="test")
    agent = SimpleAgent(config=config, llm_client=MagicMock())
    return agent


def test_parse_tasks_ordered():
    text = "1. 创建 db.py 数据库层\n2. 创建 app.py GUI层\n3. 运行测试验证功能"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3
    assert "db.py" in tasks[0]
    assert "app.py" in tasks[1]


def test_parse_tasks_dashes():
    text = "- [1] write code\n- [2] run tests\n- [3] verify"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3


def test_parse_tasks_filters_short():
    text = "1. ok\n2. create database schema with full CRUD\n3. hi"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 1
    assert "database" in tasks[0]


def test_parse_tasks_empty():
    assert DevWorkflow._parse_tasks("") == []
    assert DevWorkflow._parse_tasks("no tasks here") == []


def test_plan_task(mock_agent):
    mock_agent._llm.call.return_value = MagicMock(
        content=[MagicMock(type="text", text="## 需求分析\n做一个APP\n\n## 任务拆解\n1. 创建 db.py\n2. 创建 app.py")]
    )

    wf = DevWorkflow(mock_agent)
    plan = wf.plan_task("做一个进销存系统")

    assert "需求分析" in plan or "任务" in plan
    assert len(wf.tasks) >= 2


def test_execute_tasks(mock_agent):
    # Plan phase: returns plan
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="## 任务拆解\n1. 创建文件\n2. 测试")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="file created")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="tests pass")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build something")
    result = wf.execute(max_steps_per_task=1)

    assert "completed" in wf.report.status or "passed" in result.lower() or wf.report.status == "completed"
