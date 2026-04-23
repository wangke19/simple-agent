from __future__ import annotations

import logging
from pathlib import Path

from simple_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WriteTool(BaseTool):
    name = "file_write"
    description = "创建或覆盖文件。自动创建父目录。path参数为文件路径。"

    def __init__(self, working_dir: str | Path = ".") -> None:
        self._working_dir = Path(working_dir).resolve()

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目目录），例如 db.py 或 src/app.py"},
                "content": {"type": "string", "description": "要写入文件的完整内容"},
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs) -> str:
        logger.debug("WriteTool kwargs: %s", list(kwargs.keys()))
        path_str = kwargs.get("path") or kwargs.get("filename") or kwargs.get("file_path", "")
        content = kwargs.get("content") or kwargs.get("text", "")

        if not path_str:
            return "错误：未提供文件路径（path参数）"

        path = self._resolve(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {path_str}"

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        return resolved
