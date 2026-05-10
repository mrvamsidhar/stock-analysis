"""REST endpoints for backtests.

POST /backtests/run        Run a strategy and persist the result
GET  /backtests/{id}       Fetch a stored run (full result + equity curve)
GET  /backtests            List recent runs (summary, no equity curve)
"""
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.backtester.engine import STRATEGY_REGISTRY
from app.backtester.schemas import (
    BacktestRequest,
    BacktestRun,
    BacktestRunSummary,
)
from app.db import get_pool
from app.repositories.backtests import get_run, list_recent_runs, save_run
from app.repositories.prices import fetch_prices, ticker_exists

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/run", response_model=BacktestRun, status_code=status.HTTP_201_CREATED)
async def run_backtest(
    request: BacktestRequest,
    pool=Depends(get_pool),
) -> BacktestRun:
    """Execute a backtest and persist the result.

    Returns 400 if the strategy name is unknown or date range is invalid.
    Returns 404 if the ticker doesn't exist in our database.
    Returns 422 if the request body is malformed (FastAPI handles automatically).
    Returns 201 with the full BacktestRun on success.
    """
    ticker = request.ticker.upper()

    # Validate the strategy name.
    if request.strategy_name not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown strategy: '{request.strategy_name}'. "
                f"Known strategies: {sorted(STRATEGY_REGISTRY.keys())}"
            ),
        )

    # Validate the date range.
    if request.start_date >= request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before end_date",
        )

    # Validate the ticker exists in our DB.
    if not await ticker_exists(ticker):
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")

    # Fetch prices for the requested range.
    bars = await fetch_prices(ticker, request.start_date, request.end_date)
    if not bars:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No price data found for {ticker} between "
                f"{request.start_date} and {request.end_date}"
            ),
        )

    # Convert to DataFrame for the engine.
    df = pd.DataFrame(
        [{"close": bar["close"]} for bar in bars],
        index=pd.DatetimeIndex([bar["time"] for bar in bars]),
    )

    # Look up strategy function and run it.
    strategy_fn = STRATEGY_REGISTRY[request.strategy_name]
    try:
        result = strategy_fn(
            prices=df,
            ticker=ticker,
            initial_capital=request.initial_capital,
            **request.strategy_params,
        )
    except (ValueError, TypeError) as e:
        # ValueError: engine validation (e.g., not enough bars for SMA).
        # TypeError: bad strategy_params (e.g., unknown kwarg).
        raise HTTPException(status_code=400, detail=str(e))

    # Persist and return.
    return await save_run(
        pool=pool,
        result=result,
        strategy_params=request.strategy_params,
    )


@router.get("/{run_id}", response_model=BacktestRun)
async def get_backtest_run(
    run_id: UUID,
    pool=Depends(get_pool),
) -> BacktestRun:
    """Fetch a stored backtest run by id."""
    run = await get_run(pool=pool, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Backtest run {run_id} not found")
    return run


@router.get("", response_model=list[BacktestRunSummary])
async def list_backtests(
    limit: int = Query(default=50, ge=1, le=200),
    pool=Depends(get_pool),
) -> list[BacktestRunSummary]:
    """List recent backtest runs (most recent first), summary form."""
    return await list_recent_runs(pool=pool, limit=limit)