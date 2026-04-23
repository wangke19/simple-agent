import subprocess
from unittest.mock import patch

import pytest

from simple_agent.exceptions import ToolError
from simple_agent.tools.git import GitTool


@pytest.fixture
def tool():
    return GitTool()


def test_properties(tool):
    assert tool.name == "git"
    assert "git" in tool.description.lower()


def test_execute_status(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "status"], returncode=0, stdout="On branch main\nnothing to commit", stderr=""
        )
        result = tool.execute("git status")
        assert "main" in result


def test_execute_auto_prepends_git(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
        tool.execute("log --oneline")
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == "git log --oneline"


def test_execute_diff(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="+new line\n-old line", stderr=""
        )
        result = tool.execute("git diff")
        assert "+new line" in result


def test_execute_empty_output(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        result = tool.execute("git stash list")
        assert result == "(no output)"


def test_git_error(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="", stderr="fatal: not a git repository"
        )
        with pytest.raises(ToolError, match="not a git repository"):
            tool.execute("git status")


def test_disallowed_command(tool):
    with pytest.raises(ToolError, match="not allowed"):
        tool.execute("git push --force")


def test_disallowed_reset(tool):
    with pytest.raises(ToolError, match="not allowed"):
        tool.execute("git reset --hard")


def test_disallowed_rm(tool):
    with pytest.raises(ToolError, match="not allowed"):
        tool.execute("git rm -rf .")


def test_timeout(tool):
    with patch("simple_agent.tools.git.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git log", timeout=30)
        with pytest.raises(ToolError, match="timed out"):
            tool.execute("git log")


def test_allowed_commands_cover_readonly():
    from simple_agent.tools.git import ALLOWED_COMMANDS
    assert "status" in ALLOWED_COMMANDS
    assert "log" in ALLOWED_COMMANDS
    assert "diff" in ALLOWED_COMMANDS
    assert "branch" in ALLOWED_COMMANDS
    assert "show" in ALLOWED_COMMANDS
    assert "remote" in ALLOWED_COMMANDS
    assert "push" not in ALLOWED_COMMANDS
    assert "reset" not in ALLOWED_COMMANDS
    assert "checkout" not in ALLOWED_COMMANDS
