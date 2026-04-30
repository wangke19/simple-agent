# Engineering Standards

## Required Project Elements
Every generated project MUST have:
- Entry point (main.py / app.py / index.ts / etc.)
- Dependency declaration (requirements.txt / package.json / pyproject.toml)
- AGENT.md (project-specific rules — this file)
- tests/ directory (even if minimal)
- .gitignore

## Quality Gates
- All Python files must pass import check (no syntax or import errors)
- Database projects: schema file is single source of truth for all SQL
- Smoke test must pass (app starts without crash)
- AGENT.md must not be modified or deleted during task execution

## Code Standards
- No placeholder code (TODO, FIXME, pass-only function bodies)
- No hardcoded secrets or credentials
- Error messages must be user-friendly, not raw exceptions
- Use descriptive variable and function names