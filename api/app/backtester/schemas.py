"""Pydantic models for backtest results.

Why this file exists:
- The backtester's output is the contract between the engine and everything
  downstream (tests, future API, future UI).
- Defining it as Pydantic gives us type validation, JSON serialization,
  and OpenAPI docs for free when we add the API endpoint in Checkpoint F.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EquityPoint(BaseModel):
    """One point on the equity curve: portfolio value on a specific date."""

    date: date
    value: float = Field(ge=0, description="Portfolio value in dollars; never negative.")


class BacktestResult(BaseModel):
    """Result of running a strategy over a price series.

    Field history:
        Checkpoint A: ticker, strategy_name, dates, capital, total_return
        Checkpoint B: + num_trades
        Checkpoint C: + max_drawdown, sharpe_ratio, equity_curve, is_open_at_end
    """

    ticker: str
    strategy_name: str
    start_date: date
    end_date: date
    initial_capital: float = Field(
        gt=0,
        description="Starting cash, in dollars. Always positive."
    )
    final_value: float = Field(
        ge=0,
        description="Portfolio value at end of backtest. Can be 0 (bankrupt) but never negative."
    )
    total_return: float = Field(
        description="(final_value / initial_capital) - 1. Can be negative."
    )
    num_trades: int = Field(
        default=0,
        ge=0,
        description="Total round-trips (buy + matching sell counts as 1 trade)."
    )
    max_drawdown: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Worst peak-to-trough decline of the equity curve, expressed as a "
            "positive magnitude. 0.20 = lost 20% from peak at worst point."
        ),
    )
    sharpe_ratio: float = Field(
        default=0.0,
        description=(
            "Annualized Sharpe ratio (risk_free=0, 252 trading days/year). "
            "Higher is better. Roughly: <0=bad, 0-1=mediocre, 1-2=good, >2=excellent. "
            "Returns 0 if returns have no variance (e.g., never traded)."
        ),
    )
    equity_curve: list[EquityPoint] = Field(
        default_factory=list,
        description="Portfolio value at end of each bar, oldest first.",
    )
    is_open_at_end: bool = Field(
        default=False,
        description=(
            "True if strategy was holding shares at end of backtest. "
            "When True, final_value is mark-to-market, not realized."
        ),
    )

class BacktestRun(BaseModel):
    """A persisted BacktestResult with database-assigned metadata.

    BacktestResult is what the engine produces (in memory).
    BacktestRun is what the database stores (with id and timestamps).
    The result lives inside, so callers can access run.result.total_return
    or run.id depending on what they need.
    """

    id: UUID
    strategy_params: dict
    result: BacktestResult
    created_at: datetime