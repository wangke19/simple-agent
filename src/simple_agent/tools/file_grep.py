from __future__ import annotations

import re
from pathlib import Path

from simple_agent.tools.base import BaseTool


class GrepTool(BaseTool):
    name = "file_grep"
    description = "搜索文件内容，支持正则表达式和文件名过滤。返回匹配的文件路径和行内容。"

    def __init__(self, working_dir: str | Path = ".") -> None:
        self._working_dir = Path(working_dir).resolve()

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "搜索的正则表达式"},
                "glob": {"type": "string", "description": "文件名过滤（如 *.py），可选，默认所有文件"},
                "path": {"type": "string", "description": "搜索目录（相对于项目目录），可选，默认为项目根目录"},
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
