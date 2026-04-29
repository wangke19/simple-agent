from __future__ import annotations

import logging
from pathlib import Path

from simple_agent.skills.loader import Skill, load_skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self._skills: dict[str, Skill] = {}
        self._load_all(skills_dir)

    def _load_all(self, skills_dir: Path) -> None:
        if not skills_dir.is_dir():
            logger.debug("Skills directory not found: %s", skills_dir)
            return

        for path in skills_dir.rglob("*.md"):
            try:
                skill = load_skill(path)
                self._skills[skill.full_id] = skill
                logger.debug("Loaded skill: %s", skill.full_id)
            except Exception as e:
                logger.warning("Failed to load skill %s: %s", path, e)

    def get(self, skill_id: str) -> Skill:
        if skill_id in self._skills:
            return self._skills[skill_id]
        for skill in self._skills.values():
            if skill.name == skill_id:
                return skill
        raise KeyError(f"Unknown skill: '{skill_id}'")

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def skill_descriptions(self) -> str:
        if not self._skills:
            return "No skills available."
        lines = []
        for skill in self._skills.values():
            lines.append(f"- {skill.full_id} - {skill.description}")
        return "\n".join(lines)
