import subprocess
from unittest.mock import patch

import pytest

from simple_agent.exceptions import ToolError
from simple_agent.tools.bash import BashTool


@pytest.fixture
def tool():
    return BashTool(working_dir=".")


def test_execute_simple_command(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="hello\n", stderr=""
        )
        result = tool.execute(command="echo hello")
        assert result == "hello"


def test_execute_with_stderr(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="out", stderr="err"
        )
        result = tool.execute(command="test")
        assert "out" in result
        assert "STDERR:\nerr" in result


def test_execute_nonzero_exit(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error msg"
        )
        result = tool.execute(command="false")
        assert "Exit code: 1" in result


def test_execute_empty_output(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        result = tool.execute(command="true")
        assert result == "(no output)"


def test_timeout(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=5)
        with pytest.raises(ToolError, match="timed out"):
            tool.execute(command="sleep 100", timeout=5)


def test_custom_timeout_in_kwargs(tool):
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        tool.execute(command="test", timeout=10)
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["timeout"] == 10


def test_blocked_rm_rf(tool):
    with pytest.raises(ToolError, match="Blocked"):
        tool.execute(command="rm -rf /")


def test_blocked_mkfs(tool):
    with pytest.raises(ToolError, match="Blocked"):
        tool.execute(command="mkfs.ext4 /dev/sda1")


def test_blocked_dd(tool):
    with pytest.raises(ToolError, match="Blocked"):
        tool.execute(command="dd if=/dev/zero of=/dev/sda")


def test_allowed_commands(tool):
    """Common safe commands should not be blocked."""
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        for cmd in ["ls", "git status", "python -m pytest", "cat file.txt"]:
            result = tool.execute(command=cmd)
            assert "ok" in result


def test_parameters_schema():
    schema = BashTool().parameters
    assert "command" in schema["properties"]
    assert schema["required"] == ["command"]


def test_working_dir_passed():
    tool = BashTool(working_dir="/tmp")
    with patch("simple_agent.tools.bash.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        tool.execute(command="ls")
        assert mock_run.call_args.kwargs["cwd"] == "/tmp"
