"""Pydantic models for request/response shapes.

Why this file exists:
- Pydantic models = the contract between the API and its callers.
- Type checking, validation, and JSON serialization in one place.
- FastAPI uses these models to auto-generate the /docs schema.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class PriceBar(BaseModel):
    """One row of OHLCV data."""

    # alias: DB column is `time`, but API consumers expect `timestamp`.
    # populate_by_name=True (below) lets us construct from either name.
    timestamp: datetime = Field(validation_alias="time")
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None

    model_config = {
        "populate_by_name": True,
    }


class PricesResponse(BaseModel):
    """Response envelope for /stocks/{ticker}/prices."""

    ticker: str
    count: int
    prices: list[PriceBar]