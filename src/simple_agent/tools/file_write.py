from __future__ import annotations

from pathlib import Path

from simple_agent.tools.base import BaseTool


class WriteTool(BaseTool):
    name = "file_write"
    description = "创建或覆盖文件。自动创建父目录。"

    def __init__(self, working_dir: str | Path = ".") -> None:
        self._working_dir = Path(working_dir).resolve()

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目目录）"},
                "content": {"type": "string", "description": "要写入的内容"},
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs) -> str:
        path = self._resolve(kwargs["path"])
        content = kwargs["content"]

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {kwargs['path']}"

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        return resolved
