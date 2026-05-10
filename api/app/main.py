"""FastAPI app entry point.

Lifespan:
- On startup: open the DB connection pool.
- On shutdown: close it cleanly.
- Without this, asyncpg leaks connections when uvicorn restarts in --reload mode.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import connect_to_db, close_db_connection
from app.routers import backtests, health, stocks, tickers


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

# CORS: allow the Next.js dev server to call this API from the browser.
# Tighten this for production — only the real frontend domain should be listed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET","POST"],  # only GET for now; expand when we add POST/PUT
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(backtests.router)
app.include_router(tickers.router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "stock-analysis-api"}