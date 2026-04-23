from __future__ import annotations

import re
from pathlib import Path

from simple_agent.tools.base import BaseTool


class GrepTool(BaseTool):
    name = "file_grep"

    def __init__(self, working_dir: str | Path = ".", description: str | None = None) -> None:
        super().__init__(description=description)
        self._working_dir = Path(working_dir).resolve()

    @property
    def _default_description(self) -> str:
        return "Search file contents with regex. Supports glob pattern filtering."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "glob": {"type": "string", "description": "Filename filter (e.g. *.py), optional, default all files"},
                "path": {"type": "string", "description": "Search directory (relative to project), optional, default root"},
            },
            "required": ["pattern"],
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs["pattern"]
        glob = kwargs.get("glob", "*")
        search_path = self._resolve(kwargs.get("path", "."))

        if not search_path.is_dir():
            raise ValueError(f"Not a directory: {kwargs.get('path', '.')}")

        regex = re.compile(pattern)
        results: list[str] = []

        for file_path in sorted(search_path.rglob(glob)):
            if not file_path.is_file():
                continue
            if any(part.startswith(".") for part in file_path.relative_to(search_path).parts):
                continue
            try:
                for i, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                    if regex.search(line):
                        rel = file_path.relative_to(self._working_dir)
                        results.append(f"{rel}:{i}: {line.rstrip()}")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not results:
            return "No matches found"
        return "\n".join(results[:100])

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        return resolved
