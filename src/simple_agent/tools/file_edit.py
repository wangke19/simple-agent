from __future__ import annotations

from pathlib import Path

from simple_agent.tools.base import BaseTool


class EditTool(BaseTool):
    name = "file_edit"
    description = "精确替换文件中的字符串。需要提供old_string和new_string，old_string必须在文件中唯一匹配。"

    def __init__(self, working_dir: str | Path = ".") -> None:
        self._working_dir = Path(working_dir).resolve()

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目目录）"},
                "old_string": {"type": "string", "description": "要替换的原始字符串"},
                "new_string": {"type": "string", "description": "替换后的新字符串"},
            },
            "required": ["path", "old_string", "new_string"],
        }

    def execute(self, **kwargs) -> str:
        path = self._resolve(kwargs.get("path") or kwargs.get("filename") or kwargs.get("file_path", ""))
        old = kwargs["old_string"]
        new = kwargs["new_string"]

        content = path.read_text(encoding="utf-8")
        count = content.count(old)
        if count == 0:
            raise ValueError(f"old_string not found in {kwargs['path']}")
        if count > 1:
            raise ValueError(f"old_string matches {count} times in {kwargs['path']}, must be unique")

        updated = content.replace(old, new, 1)
        path.write_text(updated, encoding="utf-8")
        return f"Replaced 1 occurrence in {kwargs['path']}"

    def _resolve(self, path: str) -> Path:
        resolved = (self._working_dir / path).resolve()
        if not str(resolved).startswith(str(self._working_dir)):
            raise ValueError(f"Path escapes working directory: {path}")
        if not resolved.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return resolved
