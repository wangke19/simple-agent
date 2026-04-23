from __future__ import annotations

from pathlib import Path

from simple_agent.tools.base import BaseTool


class MemoryTool(BaseTool):
    name = "memory"
    description = "保存、回忆或删除跨会话的关键信息。支持 save（保存）、recall（回忆所有）、forget（按关键词删除）三种操作。"

    def __init__(self, memory_dir: str | Path = ".agent") -> None:
        self._memory_dir = Path(memory_dir)
        self._memory_file = self._memory_dir / "memory.md"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["save", "recall", "forget"],
                    "description": "操作类型：save保存，recall回忆所有，forget按关键词删除",
                },
                "content": {
                    "type": "string",
                    "description": "save时为要保存的内容，forget时为要匹配的关键词",
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs) -> str:
        action = kwargs["action"]
        if action == "save":
            return self._save(kwargs["content"])
        elif action == "recall":
            return self._recall()
        elif action == "forget":
            return self._forget(kwargs["content"])
        return f"Unknown action: {action}"

    def _save(self, content: str) -> str:
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        existing = self._read_all()
        entry = f"- {content.strip()}\n"
        if existing:
            self._memory_file.write_text(existing + entry, encoding="utf-8")
        else:
            self._memory_file.write_text(entry, encoding="utf-8")
        return f"Saved: {content.strip()}"

    def _recall(self) -> str:
        content = self._read_all()
        if not content:
            return "(no memories)"
        return content.strip()

    def _forget(self, keyword: str) -> str:
        content = self._read_all()
        if not content:
            return "Nothing to forget"
        lines = content.strip().split("\n")
        kept = [line for line in lines if keyword.lower() not in line.lower()]
        removed = len(lines) - len(kept)
        self._memory_file.write_text("\n".join(kept) + "\n", encoding="utf-8")
        return f"Removed {removed} entries matching '{keyword}'"

    def _read_all(self) -> str:
        if not self._memory_file.exists():
            return ""
        return self._memory_file.read_text(encoding="utf-8")

    def load_into_system_prompt(self) -> str:
        """Load memories as a section for the system prompt."""
        content = self._read_all()
        if not content:
            return ""
        return f"\n\n你记住的信息：\n{content.strip()}"
