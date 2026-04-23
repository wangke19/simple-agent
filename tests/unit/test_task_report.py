import pytest
from pathlib import Path

from simple_agent.task_report import TaskReport, StepRecord, StepStatus


class TestStepRecord:
    def test_auto_timestamp(self):
        record = StepRecord(step=1, action="tool_call", tool_name="bash")
        assert record.timestamp  # not empty


class TestTaskReport:
    def test_basic_report(self):
        report = TaskReport(task="build app")
        report.add_step(action="tool_call", tool_name="file_write", tool_input={"path": "a.py"}, result="ok")
        report.add_step(action="answer", result="done", status=StepStatus.SUCCESS)

        assert report.total_steps == 2
        assert report.tool_calls == 1
        assert report.failed_steps == 0

    def test_failed_steps_count(self):
        report = TaskReport(task="test")
        report.add_step(action="tool_call", tool_name="bash", status=StepStatus.FAILED, error="timeout")
        report.add_step(action="tool_call", tool_name="bash", status=StepStatus.FAILED, error="timeout")
        report.add_step(action="tool_call", tool_name="bash", status=StepStatus.SUCCESS, result="ok")

        assert report.failed_steps == 2

    def test_to_markdown(self):
        report = TaskReport(task="build app", plan="1. write db.py\n2. write app.py")
        report.add_step(action="tool_call", tool_name="file_write", tool_input={"path": "db.py"}, result="ok")
        report.add_step(action="tool_call", tool_name="bash", tool_input={"command": "python db.py"}, result="ok")
        report.status = "completed"
        report.final_result = "App built"

        md = report.to_markdown()
        assert "build app" in md
        assert "Plan" in md
        assert "file_write" in md
        assert "bash" in md
        assert "Checklist" in md
        assert "App built" in md

    def test_to_markdown_paused(self):
        report = TaskReport(task="test", status="paused", pause_reason="3 failures")
        report.add_step(action="tool_call", tool_name="bash", status=StepStatus.FAILED, error="err")
        md = report.to_markdown()
        assert "paused" in md
        assert "Human Guidance" in md
        assert "3 failures" in md

    def test_save(self, tmp_path):
        report = TaskReport(task="save test")
        report.add_step(action="answer", result="done")
        report.status = "completed"

        path = tmp_path / "reports" / "test.md"
        report.save(path)
        assert path.exists()
        content = path.read_text()
        assert "save test" in content

    def test_empty_report(self):
        report = TaskReport(task="empty")
        md = report.to_markdown()
        assert "empty" in md
        assert report.total_steps == 0
        assert report.failed_steps == 0
