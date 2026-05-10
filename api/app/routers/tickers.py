"""Ticker discovery endpoint.

GET /tickers - returns all tickers that have data in our database.
This is the single source of truth for "which tickers does the system support?"
"""
from fastapi import APIRouter

from app.repositories import prices as prices_repo

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("", response_model=list[str])
async def list_tickers() -> list[str]:
    """Return all distinct tickers in the prices table, sorted alphabetically."""
    return await prices_repo.list_tickers()