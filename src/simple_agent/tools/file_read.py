from __future__ import annotations

from pathlib import Path

from simple_agent.tools.base import BaseTool


class ReadTool(BaseTool):
    name = "file_read"

    def __init__(self, working_dir: str | Path = ".", description: str | None = None) -> None:
        super().__init__(description=description)
        self._working_dir = Path(working_dir).resolve()

    @property
    def _default_description(self) -> str:
        return "Read file contents with optional line range. Returns content with line numbers."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to project directory)"},
                "offset": {"type": "integer", "description": "Starting line number (1-based), optional"},
                "limit": {"type": "integer", "description": "Number of lines to read, optional"},
            },
            "required": ["path"],
        }

    def execute(self, **kwargs) -> str:
        path = self._resolve(kwargs.get("path") or kwargs.get("filename") or kwargs.get("file_path", ""))
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
