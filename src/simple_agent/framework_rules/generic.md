# Generic Coding Rules

## Error Handling
- Catch specific exceptions, never bare `except:`
- Display user-friendly error messages, not raw tracebacks
- Log errors with context (what operation, what inputs)

## Security
- No hardcoded secrets, credentials, or API keys
- Validate all user input at system boundaries
- Use parameterized SQL queries — never string interpolation
- Sanitize data before displaying in UI or HTML

## Code Quality
- No placeholder code: no empty `pass`, no `TODO`, no `FIXME`
- Functions should do one thing and have descriptive names
- Avoid magic numbers — use named constants
- Keep imports clean: no unused imports