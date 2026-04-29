# Skill Call System Design

## Overview

Add prompt-based skill calling to simple-agent. Skills are named prompt templates that inject specialized instructions into the agent's conversation. The LLM decides when to activate a skill by calling a `use_skill` tool.

## Approach

**Skill as a Tool** - Register a `use_skill` tool in the existing `ToolRegistry`. When the LLM calls it, the tool loads the skill's prompt content and returns it as a tool result. The LLM then follows the skill's instructions for the rest of the conversation.

This fits naturally into the existing tool system with minimal agent changes.

## Skill File Format

Skills are Markdown files with YAML frontmatter in a `skills/` directory:

```markdown
---
name: brainstorming
namespace: superpowers
description: >
  Use before any creative work - creating features, building components,
  adding functionality. Explores user intent and requirements before implementation.
---

# Brainstorming

[Skill prompt body - the instructions injected when the skill is activated]
```

- `namespace` is optional (defaults to empty string). Skills without a namespace are referenced by name only (e.g., `debug`)
- `namespace` + `name` = full skill ID (e.g., `superpowers:brainstorming`)
- `description` is shown to the LLM in the tool description to help it decide when to use the skill
- The Markdown body is the prompt content returned when the skill is activated

Files are auto-discovered recursively from the `skills/` directory, supporting subdirectories for organization.

## Module Structure

```
src/simple_agent/skills/
├── __init__.py       # Public exports (SkillRegistry, Skill, UseSkillTool)
├── registry.py       # SkillRegistry - loads and manages skills
├── loader.py         # Parses skill Markdown files (frontmatter + body)
└── tool.py           # UseSkillTool - BaseTool subclass for skill activation

skills/
└── superpowers/
    ├── brainstorming.md
    └── writing-plans.md
```

## Components

### SkillRegistry (`registry.py`)

- `SkillRegistry(skills_dir: Path)` - scans directory on init
- `get(skill_id: str) -> Skill` - lookup by full ID or short name
- `list_skills() -> list[Skill]` - all loaded skills
- `skill_descriptions() -> str` - formatted list for tool description

### Skill (dataclass)

- `name: str` - skill name
- `namespace: str` - namespace prefix
- `description: str` - one-line description for the LLM
- `content: str` - full prompt body
- `full_id: str` - computed property: `{namespace}:{name}`
- `source_path: Path` - original file path

### Skill Loader (`loader.py`)

- `load_skill(path: Path) -> Skill` - parse frontmatter + body
- Uses Python's `yaml` for frontmatter parsing
- Validates required fields (name, description)

### UseSkillTool (`tool.py`)

- Extends `BaseTool` with `name = "use_skill"`
- Takes `skill_name` (required) and `args` (optional) parameters
- `execute()` looks up the skill in `SkillRegistry`, returns formatted content
- If `args` is provided, it's appended to the skill content as a "User context" section so the skill instructions can reference it
- Dynamic description includes list of available skills

## Tool Integration

### UseSkillTool Parameters

```json
{
  "name": "use_skill",
  "description": "Activate a named skill to inject specialized instructions.\n\nAvailable skills:\n- superpowers:brainstorming - ...\n- superpowers:writing-plans - ...",
  "parameters": {
    "type": "object",
    "properties": {
      "skill_name": {"type": "string", "description": "Full skill ID or short name"},
      "args": {"type": "string", "description": "Optional arguments for the skill"}
    },
    "required": ["skill_name"]
  }
}
```

### Agent Flow

1. LLM sees `use_skill` tool with available skill descriptions
2. LLM calls `use_skill(skill_name="superpowers:brainstorming")`
3. `UseSkillTool.execute()` loads skill content from `SkillRegistry`
4. Formatted prompt returned as tool result string
5. LLM processes the skill instructions and follows them
6. Conversation continues with skill instructions in context

### Agent Integration

No changes to `agent.py` core loop. The `UseSkillTool` is registered like any other tool:

```python
skill_registry = SkillRegistry(skills_dir=Path("skills"))
use_skill_tool = UseSkillTool(skill_registry=skill_registry)
agent.register_tool(use_skill_tool)
```

## Built-in Skills

### superpowers:brainstorming

A skill for designing features/projects through collaborative dialogue:

1. Explore project context (read files, check recent commits)
2. Ask clarifying questions one at a time
3. Propose 2-3 approaches with trade-offs
4. Present design in sections, get user approval
5. Write design doc once approved

### superpowers:writing-plans

A skill for creating implementation plans from an approved design spec:

1. Read the design spec
2. Break work into ordered, testable tasks
3. Identify dependencies between tasks
4. Output a step-by-step implementation plan

## Testing Strategy

- Unit tests for `SkillLoader`: frontmatter parsing, missing fields, empty body
- Unit tests for `SkillRegistry`: loading, lookup by full ID, lookup by short name, duplicate detection
- Unit tests for `UseSkillTool`: skill activation, unknown skill error, args passing
- Integration test: agent with skill tool, verify skill content flows through conversation

## Dependencies

- `pyyaml` for YAML frontmatter parsing (add to pyproject.toml)
