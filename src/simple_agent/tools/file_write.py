from __future__ import annotations

import logging
from pathlib import Path

from simple_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WriteTool(BaseTool):
    name = "file_write"

    def __init__(self, working_dir: str | Path = ".", description: str | None = None) -> None:
        super().__init__(description=description)
        self._working_dir = Path(working_dir).resolve()

    @property
    def _default_description(self) -> str:
        return "Create or overwrite a file. Automatically creates parent directories."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to project directory), e.g. db.py or src/app.py"},
                "content": {"type": "string", "description": "Full content to write to the file"},
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs) -> str:
        logger.debug("WriteTool kwargs: %s", list(kwargs.keys()))
        path_str = kwargs.get("path") or kwargs.get("filename") or kwargs.get("file_path", "")
        content = kwargs.get("content") or kwargs.get("text", "")

        if not path_str:
            return "Error: file path not provided (path parameter)"

        path = self._resolve(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {path_str}"

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        return resolved
