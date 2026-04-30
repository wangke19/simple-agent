# Flask Rules

## Session Security
- Always set `SECRET_KEY` from environment variable, never hardcode
- Use `Flask.session` for user sessions, not cookies directly
- Set `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True` in production

## SQL Injection Prevention
- Always use parameterized queries with `?` placeholders
- Never use f-strings or string formatting for SQL queries
- Use SQLAlchemy or raw parameterized queries

## Blueprint Organization
- Use Flask Blueprints to organize routes by feature
- Register blueprints with `url_prefix` in `create_app()` factory
- Keep route handlers thin — business logic in service layer

## Error Handling
- Register error handlers with `@app.errorhandler(404)` etc.
- Return consistent JSON error responses for API endpoints