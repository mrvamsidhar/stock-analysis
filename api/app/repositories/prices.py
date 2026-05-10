"""Price data access. SQL lives here, nowhere else.

Why this file exists:
- Routers handle HTTP concerns (parsing query strings, returning status codes).
- Repositories handle data concerns (SQL queries, DB connections).
- Keeping them separate means: when you tune a query, you only touch
  this file. When you change an HTTP response shape, you only touch
  the router. Each file has one reason to change.
"""
from datetime import date
from typing import Any

from app.db import get_pool


# Parameterized query. NEVER use f-strings or string concatenation for SQL —
# that's how SQL injection happens. asyncpg uses $1, $2, $3 for parameters.
_FETCH_PRICES_SQL = """
    SELECT time, open, high, low, close, volume
    FROM prices
    WHERE ticker = $1
      AND time >= $2
      AND time <= $3
    ORDER BY time ASC;
"""

_TICKER_EXISTS_SQL = """
    SELECT EXISTS(
        SELECT 1 FROM prices WHERE ticker = $1 LIMIT 1
    );
"""


async def ticker_exists(ticker: str) -> bool:
    """Return True if the ticker has any rows in the prices table."""
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(_TICKER_EXISTS_SQL, ticker.upper())

async def fetch_prices(
    ticker: str,
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    """Fetch OHLCV rows for a ticker between start and end (inclusive).

    Returns a list of dicts with keys: time, open, high, low, close, volume.
    Empty list if no data — that is NOT an error condition; it just means
    no rows in range. The router decides what to do about that.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(_FETCH_PRICES_SQL, ticker.upper(), start, end)
    # asyncpg.Record objects behave dict-like but aren't dicts. Convert
    # explicitly so the rest of the app deals with plain Python types.
    return [dict(row) for row in rows]

_LIST_TICKERS_SQL = """
    SELECT DISTINCT ticker
    FROM prices
    ORDER BY ticker ASC;
"""


async def list_tickers() -> list[str]:
    """Return all distinct tickers with at least one row in the prices table.

    Used by the frontend to populate "which ticker?" dropdowns. Single
    source of truth: a ticker exists if and only if we have data for it.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(_LIST_TICKERS_SQL)
    return [row["ticker"] for row in rows]