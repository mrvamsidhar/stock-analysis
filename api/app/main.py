"""FastAPI app entry point.

Lifespan:
- On startup: open the DB connection pool.
- On shutdown: close it cleanly.
- Without this, asyncpg leaks connections when uvicorn restarts in --reload mode.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers import health, stocks
from app.db import connect_to_db, close_db_connection
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_db()
    yield
    # Shutdown
    await close_db_connection()


app = FastAPI(
    title="Stock Analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(stocks.router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "stock-analysis-api"}