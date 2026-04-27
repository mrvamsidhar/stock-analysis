"""Health check endpoint.

Why /health exists:
- Lets you (and later, deployment systems) verify the API is alive AND
  can reach its dependencies. An API that returns 200 but can't talk to
  the DB is worse than one that returns 503 honestly.
- /health does a real round-trip: SELECT 1. If the DB is down, /health
  returns 503 with a clear message.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db import get_pool

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Verify the API is up and the database is reachable."""
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1;")
        if result != 1:
            raise RuntimeError(f"Unexpected health probe result: {result}")
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "unreachable", "error": str(exc)},
        )