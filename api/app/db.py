"""Async database connection pool.

Why a pool and not a single connection:
- Each HTTP request that needs the DB borrows a connection from the pool,
  uses it, and returns it. The pool reuses connections instead of opening
  a fresh one per request (which would be 5-10x slower).
- Pool is created at app startup, closed at app shutdown.
- For a single-developer Phase 2 project, pool size of 5-10 is plenty.
"""
import asyncpg
from app.config import settings


# Module-level pool. Set during app startup, used everywhere.
_pool: asyncpg.Pool | None = None


async def connect_to_db() -> None:
    """Create the connection pool. Called once at app startup."""
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=10,  # seconds; queries that hang fail fast
    )


async def close_db_connection() -> None:
    """Close the pool. Called once at app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Return the active pool. Raises if called before startup."""
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialized. "
            "This usually means the app started without lifespan setup."
        )
    return _pool