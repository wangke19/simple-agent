---
name: writing-plans
namespace: superpowers
description: >
  Use when you have a spec or requirements for a multi-step task and need to
  create a detailed, step-by-step implementation plan before writing code.
---

# Writing Implementation Plans

Create comprehensive implementation plans from an approved design spec. Plans are bite-sized, testable tasks that an engineer can execute sequentially.

## Process

1. **Read the spec** — understand the full scope and all requirements
2. **Map file structure** — list every file that will be created or modified, with its responsibility
3. **Break into tasks** — each task is one focused change (a dataclass, a function, a test file)
4. **Order tasks** — each task depends only on tasks before it

## Task Granularity

Each step in a task is ONE action:
- Write the failing test
- Run it to see it fail
- Write minimal implementation
- Run tests to see them pass
- Commit

## Rules

- Every step must contain actual code — no placeholders, no "TBD", no "implement similar to X"
- Exact file paths always
- Complete code in every step
- TDD: test first, then implement
- Frequent small commits
- DRY and YAGNI