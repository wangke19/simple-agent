from __future__ import annotations

import subprocess

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool

ALLOWED_COMMANDS = frozenset({
    "status", "log", "diff", "branch", "remote",
    "show", "stash list", "tag",
})


def _validate(command: str) -> str:
    cmd = command.strip().lower()
    if not cmd.startswith("git "):
        cmd = f"git {cmd}"
    subcmd = cmd.removeprefix("git ").split()[0] if cmd != "git" else ""
    # allow "git log --oneline -5" but not "git push --force"
    if subcmd not in {c.split()[0] for c in ALLOWED_COMMANDS}:
        allowed = ", ".join(sorted(ALLOWED_COMMANDS))
        raise ToolError(
            f"Git subcommand '{subcmd}' is not allowed. Allowed: {allowed}"
        )
    return cmd


class GitTool(BaseTool):
    name = "git"
    description = "执行安全的只读git命令（status, log, diff, branch, show, remote, stash list, tag）"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Git命令（如 status, log --oneline -5, diff）"},
            },
            "required": ["input"],
        }

    def execute(self, **kwargs) -> str:
        cmd = _validate(kwargs.get("input", ""))
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(f"Git command timed out: {cmd}")

        if result.returncode != 0:
            raise ToolError(f"Git error: {result.stderr.strip()}")

        return result.stdout.strip() or "(no output)"
