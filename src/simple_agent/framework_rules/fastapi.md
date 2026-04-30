# FastAPI Rules

## Async Pitfalls
- Use `async def` for endpoints that do I/O (database, HTTP calls)
- Use `def` (sync) for CPU-bound endpoints — FastAPI runs them in threadpool
- Never call synchronous blocking code inside `async def` endpoints

## Pydantic v2
- Use `model_validate()` instead of deprecated `parse_obj()`
- Use `model_dump()` instead of deprecated `dict()`
- Config use `model_config = ConfigDict(...)` instead of inner `Config` class

## Dependency Injection
- Use `Depends()` for database sessions, authentication, etc.
- Keep dependency functions small and testable
- Use generator dependencies with `yield` for cleanup (e.g., DB session close)

## Type Hints
- Use Python 3.10+ union syntax: `str | None` instead of `Optional[str]`
- Return models from endpoints for automatic response serialization