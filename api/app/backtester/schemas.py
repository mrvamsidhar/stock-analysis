"""Pydantic models for backtest results.

Why this file exists:
- The backtester's output is the contract between the engine and everything
  downstream (tests, future API, future UI).
- Defining it as Pydantic gives us type validation, JSON serialization,
  and OpenAPI docs for free when we add the API endpoint in Checkpoint F.
"""
from datetime import date
from pydantic import BaseModel, Field


class BacktestResult(BaseModel):
    """Result of running a strategy over a price series.

    For Checkpoint A this only contains total_return. Checkpoints C and beyond
    will add max_drawdown, sharpe_ratio, trades, equity_curve.
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