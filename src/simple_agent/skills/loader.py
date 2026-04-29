from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Skill:
    name: str
    namespace: str
    description: str
    content: str
    source_path: Path

    @property
    def full_id(self) -> str:
        if self.namespace:
            return f"{self.namespace}:{self.name}"
        return self.name


def load_skill(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Skill file {path} has no YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Skill file {path} has malformed frontmatter")

    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise ValueError(f"Skill file {path} has invalid frontmatter")

    if "name" not in meta:
        raise ValueError(f"Skill file {path} missing required field: name")
    if "description" not in meta:
        raise ValueError(f"Skill file {path} missing required field: description")

    body = parts[2].strip()

    return Skill(
        name=meta["name"],
        namespace=meta.get("namespace", ""),
        description=meta["description"],
        content=body,
        source_path=path,
    )
