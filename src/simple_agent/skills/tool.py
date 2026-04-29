from __future__ import annotations

from typing import Any

from simple_agent.tools.base import BaseTool
from simple_agent.skills.registry import SkillRegistry


class UseSkillTool(BaseTool):
    name = "use_skill"

    def __init__(self, skill_registry: SkillRegistry, description: str | None = None) -> None:
        super().__init__(description=description)
        self._registry = skill_registry

    @property
    def _default_description(self) -> str:
        header = "Activate a named skill to inject specialized instructions into the conversation.\n\nAvailable skills:"
        return f"{header}\n{self._registry.skill_descriptions()}"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Full skill ID (e.g., 'superpowers:brainstorming') or short name",
                },
                "args": {
                    "type": "string",
                    "description": "Optional arguments to pass to the skill",
                },
            },
            "required": ["skill_name"],
        }

    def execute(self, **kwargs: Any) -> str:
        skill_name = kwargs.get("skill_name", "")
        args = kwargs.get("args", "")

        try:
            skill = self._registry.get(skill_name)
        except KeyError as e:
            return f"Error: {e}"

        result = skill.content
        if args:
            result += f"\n\n---\n## User context\n{args}"
        return result
