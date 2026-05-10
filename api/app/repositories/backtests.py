"""Repository for persisting and fetching backtest runs.

Why this file exists:
- The backtester engine produces BacktestResult objects (in-memory).
- The API layer (Phase 5.F) accepts/returns BacktestRun objects (DB-shaped).
- This file is the bridge: it serializes BacktestResult into rows on insert,
  and deserializes rows into BacktestRun on fetch.

Why raw asyncpg, not an ORM:
- Same project convention as repositories/prices.py from Phase 2.
- The queries are simple (one INSERT, one SELECT). An ORM would add machinery
  for no benefit at this scale. Boring beats shiny.
"""
import json
from typing import Optional
from uuid import UUID

import asyncpg

from app.backtester.schemas import BacktestResult, BacktestRun, BacktestRunSummary


async def save_run(
    pool: asyncpg.Pool,
    result: BacktestResult,
    strategy_params: dict,
) -> BacktestRun:
    """Persist a BacktestResult to the backtest_runs table.

    Args:
        pool: asyncpg connection pool (lifespan-managed by FastAPI).
        result: the engine output to persist.
        strategy_params: the input parameters used (e.g., {"fast_window": 50,
            "slow_window": 200}). Stored separately so we can re-create or
            reproduce the run later.

    Returns:
        BacktestRun with the DB-assigned id and created_at filled in.
    """
    # Serialize the equity curve (list of EquityPoint) into JSON for JSONB storage.
    # Pydantic's mode="json" handles date serialization correctly.
    equity_curve_json = json.dumps(
        [point.model_dump(mode="json") for point in result.equity_curve]
    )
    strategy_params_json = json.dumps(strategy_params)

    row = await pool.fetchrow(
        """
        INSERT INTO backtest_runs (
            ticker, strategy_name, strategy_params,
            start_date, end_date,
            initial_capital, final_value, total_return,
            num_trades, max_drawdown, sharpe_ratio,
            is_open_at_end, equity_curve
        )
        VALUES (
            $1, $2, $3::jsonb,
            $4, $5,
            $6, $7, $8,
            $9, $10, $11,
            $12, $13::jsonb
        )
        RETURNING id, created_at
        """,
        result.ticker,
        result.strategy_name,
        strategy_params_json,
        result.start_date,
        result.end_date,
        result.initial_capital,
        result.final_value,
        result.total_return,
        result.num_trades,
        result.max_drawdown,
        result.sharpe_ratio,
        result.is_open_at_end,
        equity_curve_json,
    )

    return BacktestRun(
        id=row["id"],
        created_at=row["created_at"],
        strategy_params=strategy_params,
        result=result,
    )


async def get_run(pool: asyncpg.Pool, run_id: UUID) -> Optional[BacktestRun]:
    """Fetch a backtest run by id.

    Returns None if no run with that id exists. Caller (the API router)
    is responsible for translating None into a 404 response.
    """
    row = await pool.fetchrow(
        """
        SELECT
            id, ticker, strategy_name, strategy_params,
            start_date, end_date,
            initial_capital, final_value, total_return,
            num_trades, max_drawdown, sharpe_ratio,
            is_open_at_end, equity_curve, created_at
        FROM backtest_runs
        WHERE id = $1
        """,
        run_id,
    )
    if row is None:
        return None

    # asyncpg returns JSONB as a Python object already (parsed), but only for
    # columns whose type is registered. equity_curve and strategy_params come
    # back as strings; we json.loads() them.
    equity_curve_data = row["equity_curve"]
    if isinstance(equity_curve_data, str):
        equity_curve_data = json.loads(equity_curve_data)

    strategy_params_data = row["strategy_params"]
    if isinstance(strategy_params_data, str):
        strategy_params_data = json.loads(strategy_params_data)

    result = BacktestResult(
        ticker=row["ticker"],
        strategy_name=row["strategy_name"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        initial_capital=row["initial_capital"],
        final_value=row["final_value"],
        total_return=row["total_return"],
        num_trades=row["num_trades"],
        max_drawdown=row["max_drawdown"],
        sharpe_ratio=row["sharpe_ratio"],
        is_open_at_end=row["is_open_at_end"],
        equity_curve=equity_curve_data,
    )

    return BacktestRun(
        id=row["id"],
        created_at=row["created_at"],
        strategy_params=strategy_params_data,
        result=result,
    )

async def list_recent_runs(
    pool: asyncpg.Pool,
    limit: int = 50,
) -> list["BacktestRunSummary"]:
    """Return the N most recent runs, summary form (no equity curve)."""
    from app.backtester.schemas import BacktestRunSummary

    rows = await pool.fetch(
        """
        SELECT
            id, ticker, strategy_name, start_date, end_date,
            total_return, num_trades, max_drawdown, sharpe_ratio,
            is_open_at_end, created_at
        FROM backtest_runs
        ORDER BY created_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [BacktestRunSummary(**dict(row)) for row in rows]