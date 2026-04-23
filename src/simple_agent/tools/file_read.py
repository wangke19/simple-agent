from __future__ import annotations

from pathlib import Path

from simple_agent.tools.base import BaseTool


class ReadTool(BaseTool):
    name = "file_read"
    description = "读取文件内容，支持指定行范围。返回带行号的文件内容。"

    def __init__(self, working_dir: str | Path = ".") -> None:
        self._working_dir = Path(working_dir).resolve()

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目目录）"},
                "offset": {"type": "integer", "description": "起始行号（从1开始），可选"},
                "limit": {"type": "integer", "description": "读取行数，可选"},
            },
            "required": ["path"],
        }

    def execute(self, **kwargs) -> str:
        path = self._resolve(kwargs["path"])
        offset = kwargs.get("offset")
        limit = kwargs.get("limit")

        lines = path.read_text(encoding="utf-8").splitlines()
        start = (offset or 1) - 1
        end = start + limit if limit else len(lines)
        selected = lines[start:end]

        return "\n".join(f"{i + start + 1}\t{line}" for i, line in enumerate(selected))

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        if not resolved.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return resolved
