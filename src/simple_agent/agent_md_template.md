# Engineering Standards

## Required Project Elements
Every generated project MUST have:
- Entry point (main.py / app.py / index.ts / etc.)
- Dependency declaration (requirements.txt / package.json / pyproject.toml)
- AGENT.md (project-specific rules — this file)
- tests/ directory (even if minimal)
- .gitignore

## File Organization
Source code, test code, build artifacts, and runtime data MUST be separated:

| Category | Location | Examples |
|----------|----------|----------|
| Source code | Project root `*.py` | `main.py`, `db_manager.py`, `*_service.py`, `*_tab.py` |
| Tests | `tests/` | `tests/smoke_test.py`, `tests/test_*.py` |
| Database schema | Root `database_init.sql` | Single source of truth for all SQL |
| Styles | Root `styles.qss` | Qt stylesheet |
| Build artifacts | `.reports/` | Workflow reports, smoke test results |
| Runtime data | Root (gitignored) | `*.db`, `test_*.db` |

Rules:
- Smoke tests go in `tests/`, NOT in the project root
- Test result reports go in `.reports/`, NOT alongside source files
- Runtime databases (`*.db`) must be in `.gitignore`
- Do NOT create ad-hoc result files in the project root (e.g. `SMOKE_TEST_RESULTS.md`, `test_import.db`)
- Do NOT create subdirectories like `src/`, `services/`, `ui/`, `views/`

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

## Data Access Rules
- `execute_read()` returns `dict` — use `row['column_name']` subscript access
- Services return `dataclass` objects (from models.py) — use `obj.field` attribute access, NOT `obj['field']`
- NEVER mix access patterns: dict subscript on a dataclass causes `TypeError: object is not subscriptable`