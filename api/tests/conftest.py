"""Shared pytest fixtures for the API test suite."""
from pathlib import Path

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import db as db_module
from app.config import settings
from app.main import app


SEED_FILE = Path(__file__).parent / "seed_data.sql"


@pytest_asyncio.fixture
async def test_pool():
    """Create a fresh test DB pool, seed it, swap it into the app module,
    yield, then restore production state.

    The `db_module._pool` swap is the trick: the app's get_pool() reads
    that module-level variable, so swapping it makes the app use the test
    DB without changing any application code.
    """
    pool = await asyncpg.create_pool(
        dsn=settings.database_url_test,
        min_size=1,
        max_size=5,
        command_timeout=10,
    )

    seed_sql = SEED_FILE.read_text()
    async with pool.acquire() as conn:
        await conn.execute(seed_sql)

    # Save whatever pool was there (probably None during tests) and swap in ours
    original_pool = db_module._pool
    db_module._pool = pool

    yield pool

    # Restore + cleanup
    db_module._pool = original_pool
    await pool.close()


@pytest_asyncio.fixture
async def client(test_pool):
    """Async HTTP client wired to the FastAPI app with the test DB active."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac