import pytest
from unittest.mock import MagicMock

from simple_agent.config import AgentConfig
from simple_agent.dev_workflow import DevWorkflow, TaskItem
from simple_agent import SimpleAgent
from simple_agent.tools.registry import ToolRegistry
from simple_agent.task_report import TaskReport, StepStatus
from tests.conftest import make_text_block, make_tool_use_block


@pytest.fixture
def mock_agent():
    config = AgentConfig(base_url="https://fake", api_key="key", model="test")
    agent = SimpleAgent(config=config, llm_client=MagicMock())
    # Create an empty tool registry so search tool calls will fail
    agent._tools = ToolRegistry()
    return agent


def test_parse_tasks_ordered():
    text = "1. 创建 db.py 数据库层\n2. 创建 app.py GUI层\n3. 运行测试验证功能"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3
    assert "db.py" in tasks[0].description
    assert "app.py" in tasks[1].description


def test_parse_tasks_dashes():
    text = "- [1] write code\n- [2] run tests\n- [3] verify"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3


def test_parse_tasks_filters_short():
    text = "1. ok\n2. create database schema with full CRUD\n3. hi"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 1
    assert "database" in tasks[0].description


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


# --- Contract phase tests ---

def test_define_contracts(mock_agent):
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="## 任务拆解\n1. 创建 db.py 数据库层\n2. 创建 app.py GUI层")]),
        # define_contracts
        MagicMock(content=[MagicMock(type="text", text="## 模块接口契约\n### db.py\n- add_product(name: str) -> int\n### app.py\n调用 db.add_product(name)")]),
    ]

    wf = DevWorkflow(mock_agent)
    wf.plan_task("build an app")
    contract = wf.define_contracts("build an app")

    assert "接口契约" in contract or "db.py" in contract
    assert len(wf.contract) > 0


def test_execute_with_contract(mock_agent):
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. 创建 db.py\n2. 创建 app.py")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="db created")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="app created")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build something")
    wf._contract = "### db.py\n- add_product(name: str, category: str) -> int"
    wf.execute(max_steps_per_task=1)

    # Verify the LLM was called with contract in the task prompt
    calls = mock_agent._llm.call.call_args_list
    # Task executions are calls[1] and calls[2]
    task1_kwargs = calls[1].kwargs
    messages = task1_kwargs.get("messages")
    user_msgs = [m for m in messages if m["role"] == "user"]
    assert any("add_product" in m.get("content", "") for m in user_msgs)


def test_execute_without_contract(mock_agent):
    mock_agent._llm.call.side_effect = [
        MagicMock(content=[MagicMock(type="text", text="1. task one\n2. task two")]),
        MagicMock(content=[MagicMock(type="text", text="done1")]),
        MagicMock(content=[MagicMock(type="text", text="done2")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("do something")
    assert wf.contract == ""
    result = wf.execute(max_steps_per_task=1)
    assert wf.report.status == "completed"


def test_full_workflow_with_contracts(mock_agent):
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="## 任务拆解\n1. 创建 db.py\n2. 创建 app.py")]),
        # decompose
        MagicMock(content=[MagicMock(type="text", text="1. 创建 db.py 数据库层\n2. 创建 app.py 界面层")]),
        # define_contracts
        MagicMock(content=[MagicMock(type="text", text="## 模块接口契约\n### db.py - Database\n- add_product(name, category, price) -> int")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="db done")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="app done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build inventory")
    wf.decompose("build inventory")
    contract = wf.define_contracts("build inventory")

    assert len(wf.tasks) == 2
    assert "db.py" in contract
    result = wf.execute(max_steps_per_task=1)
    assert wf.report.status == "completed"
    assert "API Contract" in wf.report.final_result


# --- WorkflowConfig and run_all tests ---

def test_run_all(mock_agent):
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Create db.py\n2. Create app.py")]),
        # decompose
        MagicMock(content=[MagicMock(type="text", text="1. Create db.py database layer\n2. Create app.py GUI layer")]),
        # define_contracts
        MagicMock(content=[MagicMock(type="text", text="## API Contract\ndb.py methods here")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="db done")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="app done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    result = wf.run_all("build an app")
    assert wf.report.status == "completed"


def test_workflow_config_disable_contracts(mock_agent):
    from simple_agent.dev_workflow import WorkflowConfig

    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Write code\n2. Test code")]),
        # decompose
        MagicMock(content=[MagicMock(type="text", text="1. Write some code file\n2. Run test verification")]),
        # task 1
        MagicMock(content=[MagicMock(type="text", text="code done")]),
        # task 2
        MagicMock(content=[MagicMock(type="text", text="tests pass")]),
    ]

    config = WorkflowConfig(enable_contracts=False)
    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports", workflow_config=config)
    wf.plan_task("do something")
    wf.decompose("do something")
    # Contract should be empty since we skipped define_contracts
    assert wf.contract == ""
    result = wf.execute(max_steps_per_task=1)
    assert wf.report.status == "completed"


def test_chinese_prompts_workflow(mock_agent):
    from simple_agent.prompts import chinese_prompts
    from simple_agent.messages import chinese_messages

    mock_agent._llm.call.side_effect = [
        MagicMock(content=[MagicMock(type="text", text="1. Create something useful\n2. Test everything works")]),
        MagicMock(content=[MagicMock(type="text", text="done")]),
        MagicMock(content=[MagicMock(type="text", text="done2")]),
    ]

    wf = DevWorkflow(
        mock_agent,
        report_dir="/tmp/test_reports",
        prompts=chinese_prompts(),
        messages=chinese_messages(),
    )
    wf.plan_task("build something")
    result = wf.execute(max_steps_per_task=1)
    assert wf.report.status == "completed"


# --- retry_failed tests ---

def test_retry_failed(mock_agent):
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Create db.py\n2. Create app.py\n3. Run tests")]),
        # task 1 - success
        MagicMock(content=[MagicMock(type="text", text="db done")]),
        # task 2 - fails (max steps exceeded: 2 tool calls then max_steps hits)
        MagicMock(content=[make_tool_use_block("search", {"input": "x"})]),
        MagicMock(content=[make_tool_use_block("search", {"input": "x"})]),
        # task 3 - success
        MagicMock(content=[MagicMock(type="text", text="tests pass")]),
        # retry task 2 - now succeeds
        MagicMock(content=[MagicMock(type="text", text="app created on retry")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build app")

    # Execute with task 2 failing (max_steps=2, 2 tool_use calls = max steps exceeded)
    wf.execute(max_steps_per_task=2)

    # Task 2 should be failed
    assert wf._task_results[0]["status"] == "completed"
    assert wf._task_results[1]["status"] == "failed"
    assert wf._task_results[2]["status"] == "completed"
    assert wf.failed_task_indices == [1]

    # Retry
    result = wf.retry_failed(max_steps_per_task=1)
    assert wf._task_results[1]["status"] == "completed"
    assert wf.report.status == "completed"


def test_retry_failed_no_failures(mock_agent):
    mock_agent._llm.call.side_effect = [
        MagicMock(content=[MagicMock(type="text", text="1. Simple task")]),
        MagicMock(content=[MagicMock(type="text", text="done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("simple task")
    wf.execute(max_steps_per_task=1)

    assert wf.failed_task_indices == []
    result = wf.retry_failed(max_steps_per_task=1)
    assert wf.report.status == "completed"


# --- TaskItem tests ---

def test_task_item_defaults():
    from simple_agent.dev_workflow import TaskItem

    t = TaskItem(index=1, description="Create db.py")
    assert t.depends_on == []
    assert t.retry_count == 0
    assert t.status == "pending"


def test_task_item_with_dependencies():
    from simple_agent.dev_workflow import TaskItem

    t = TaskItem(index=3, description="Create API", depends_on=[0, 1])
    assert t.depends_on == [0, 1]
    assert t.index == 3


# --- Task 2: Dependency parsing tests ---


def test_parse_tasks_with_dependencies():
    text = "1. Create db.py database layer [depends: none]\n2. Create app.py GUI [depends: 1]\n3. Run tests [depends: 1, 2]"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3
    assert isinstance(tasks[0], TaskItem)
    assert tasks[0].description == "Create db.py database layer"
    assert tasks[0].depends_on == []
    assert tasks[0].index == 1
    assert tasks[1].depends_on == [0]
    assert tasks[1].index == 2
    assert tasks[2].depends_on == [0, 1]
    assert tasks[2].index == 3


def test_parse_tasks_no_dependency_annotation_falls_back_to_sequential():
    text = "1. Create db.py database layer\n2. Create app.py GUI layer\n3. Run tests verification"
    tasks = DevWorkflow._parse_tasks(text)
    assert len(tasks) == 3
    assert tasks[0].depends_on == []
    assert tasks[1].depends_on == [0]
    assert tasks[2].depends_on == [1]


def test_parse_tasks_mixed_annotations():
    text = "1. Create db.py [depends: none]\n2. Create app.py\n3. Run tests [depends: 1, 2]"
    tasks = DevWorkflow._parse_tasks(text)
    assert tasks[0].depends_on == []
    assert tasks[1].depends_on == [0]  # fallback: depends on previous
    assert tasks[2].depends_on == [0, 1]


# --- Task 4: Retry boundary tests ---

def test_execute_tracks_retry_count_on_failure(mock_agent):
    """Failed tasks get retry_count incremented."""
    # Create a scenario where the agent makes 2 attempts but both fail, causing retry_count increment
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Task one\n2. Task two")]),
        # task 1 - first attempt with tool call (fails)
        MagicMock(content=[make_tool_use_block("search", {"input": "x"})]),
        # task 2 - success
        MagicMock(content=[MagicMock(type="text", text="done")]),
        # retry task 1 - second attempt (still fails)
        MagicMock(content=[make_tool_use_block("search", {"input": "x"})]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build something")
    wf.execute(max_steps_per_task=1)

    # Task 1 should have failed and retry_count should be 1
    task1_result = wf._task_results[0]
    assert task1_result["status"] == "failed"
    assert task1_result["retry_count"] == 1


def test_retry_failed_skips_after_3_retries_no_dependents(mock_agent):
    """Task that hit 3-retry limit with no dependents gets skipped."""
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. Independent task A\n2. Independent task B")]),
        # task 1 - succeeds
        MagicMock(content=[MagicMock(type="text", text="ok")]),
        # task 2 - succeeds
        MagicMock(content=[MagicMock(type="text", text="done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build something")
    wf.execute(max_steps_per_task=1)

    # Manually set task 1 to have 3 retries already (simulating 3 prior failures)
    wf._tasks[0].retry_count = 3
    wf._tasks[0].status = "failed"
    wf._task_results[0]["status"] = "failed"
    wf._task_results[0]["retry_count"] = 3
    # Make task 2 independent (no dependency on task 1)
    wf._tasks[1].depends_on = []

    result = wf.retry_failed(max_steps_per_task=1)
    assert wf._tasks[0].status == "skipped"
    assert wf._task_results[0]["status"] == "skipped"


def test_retry_failed_pauses_after_3_retries_with_dependents(mock_agent):
    """Task that hit 3-retry limit with dependents causes workflow to pause."""
    mock_agent._llm.call.side_effect = [
        # plan_task
        MagicMock(content=[MagicMock(type="text", text="1. DB setup [depends: none]\n2. API layer [depends: 1]")]),
        # task 1 - succeeds
        MagicMock(content=[MagicMock(type="text", text="ok")]),
        # task 2 - succeeds
        MagicMock(content=[MagicMock(type="text", text="ok")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build something")
    wf.execute(max_steps_per_task=1)

    # Manually set task 1 to have 3 retries and failed
    wf._tasks[0].retry_count = 3
    wf._tasks[0].status = "failed"
    wf._task_results[0]["status"] = "failed"
    wf._task_results[0]["retry_count"] = 3
    # Task 2 depends on task 1 and is still failed
    wf._tasks[1].depends_on = [0]
    wf._tasks[1].status = "failed"

    result = wf.retry_failed(max_steps_per_task=1)
    assert wf.report.status == "paused"


def test_finalize_report_marks_skipped_tasks(mock_agent):
    """Skipped tasks show [~] in checklist."""
    mock_agent._llm.call.side_effect = [
        MagicMock(content=[MagicMock(type="text", text="1. Task one")]),
        MagicMock(content=[MagicMock(type="text", text="done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports")
    wf.plan_task("build")
    wf.execute(max_steps_per_task=1)

    wf._task_results[0]["status"] = "skipped"
    result = wf._finalize_report()
    assert "[~]" in result


# --- New tests for _scan_written_files and _validate_task_output ---

def test_scan_written_files_from_report():
    """Extract .py filenames written during a task from agent report steps."""
    from simple_agent.task_report import TaskReport, StepRecord, StepStatus
    report = TaskReport(task="test")
    report.add_step(
        action="tool_call", tool_name="file_write",
        tool_input={"path": "database.py", "content": "pass"},
        status=StepStatus.SUCCESS,
    )
    report.add_step(
        action="tool_call", tool_name="file_write",
        tool_input={"path": "ui/main_window.py", "content": "pass"},
        status=StepStatus.SUCCESS,
    )
    report.add_step(
        action="tool_call", tool_name="bash",
        tool_input={"command": "ls"},
        status=StepStatus.SUCCESS,
    )
    files = DevWorkflow._scan_written_files(report)
    assert files == ["database.py", "ui/main_window.py"]


def test_scan_written_files_empty():
    from simple_agent.task_report import TaskReport
    report = TaskReport(task="test")
    assert DevWorkflow._scan_written_files(report) == []


def test_validate_task_output_passes(tmp_path):
    """Import check passes for a valid .py file."""
    (tmp_path / "valid.py").write_text("x = 1\n")
    report = TaskReport(task="test")
    report.add_step(
        action="tool_call", tool_name="file_write",
        tool_input={"path": "valid.py", "content": "x = 1"},
        status=StepStatus.SUCCESS,
    )
    errors = DevWorkflow._validate_task_output(report, str(tmp_path))
    assert errors == []


def test_validate_task_output_catches_import_error(tmp_path):
    """Import check fails for a file with bad import."""
    (tmp_path / "bad.py").write_text("from nonexistent_module import foo\n")
    report = TaskReport(task="test")
    report.add_step(
        action="tool_call", tool_name="file_write",
        tool_input={"path": "bad.py", "content": "from nonexistent_module import foo"},
        status=StepStatus.SUCCESS,
    )
    errors = DevWorkflow._validate_task_output(report, str(tmp_path))
    assert len(errors) == 1
    assert "bad.py" in errors[0]
    assert "nonexistent_module" in errors[0]


def test_execute_marks_failed_on_import_error(mock_agent, tmp_path):
    """Task that writes a file with import error gets marked failed."""
    (tmp_path / "bad.py").write_text("from nonexistent_module import foo\n")

    mock_agent._llm.call.side_effect = [
        MagicMock(content=[MagicMock(type="text", text="1. Create bad module")]),
        MagicMock(content=[
            make_tool_use_block("file_write", {"path": "bad.py", "content": "from nonexistent_module import foo"}),
        ]),
        MagicMock(content=[MagicMock(type="text", text="done")]),
    ]

    wf = DevWorkflow(mock_agent, report_dir="/tmp/test_reports", working_dir=str(tmp_path))
    wf.plan_task("build something")
    wf.execute(max_steps_per_task=2)

    assert wf._task_results[0]["status"] == "failed"
