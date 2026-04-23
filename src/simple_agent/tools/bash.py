from __future__ import annotations

import subprocess

from simple_agent.exceptions import ToolError
from simple_agent.tools.base import BaseTool

DENYLIST_PATTERNS = frozenset({
    "rm -rf /", "mkfs", "dd if=", "> /dev/sd",
    "chmod -R 777 /", "wget", "curl -o /", ":(){ :|:& };:",
})


class BashTool(BaseTool):
    name = "bash"
    description = "执行shell命令，返回stdout和stderr。支持设置超时时间。"

    def __init__(self, working_dir: str = ".", timeout: int = 120) -> None:
        self._working_dir = working_dir
        self._timeout = timeout

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的shell命令"},
                "timeout": {"type": "integer", "description": f"超时秒数（默认{self._timeout}）"},
            },
            "required": ["command"],
        }

    def execute(self, **kwargs) -> str:
        command = kwargs["command"]
        timeout = kwargs.get("timeout", self._timeout)

        _validate(command)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._working_dir,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {timeout}s: {command}")

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += f"STDERR:\n{result.stderr}"

        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"

        return output.strip() or "(no output)"


def _validate(command: str) -> None:
    lower = command.lower().strip()
    for pattern in DENYLIST_PATTERNS:
        if pattern in lower:
            raise ToolError(f"Blocked command (matches denylist: '{pattern}')")
