"""Backtester engine.

Why this file exists:
- Pure functions that take price data + strategy params, return BacktestResult.
- No DB access, no I/O, no globals. The function signature is the contract.
- Testability + composability over cleverness.
"""
import pandas as pd

from app.backtester.schemas import BacktestResult


def run_buy_and_hold(
    prices: pd.DataFrame,
    ticker: str,
    initial_capital: float = 10_000.0,
) -> BacktestResult:
    """Buy on the first day, hold to the last day, sell on the last day.

    Buy-and-hold is the control case. Every other strategy must beat this
    to be worth implementing. It's also the unit test for the engine itself —
    if buy-and-hold is wrong, all other strategies are wrong.

    Expected DataFrame shape:
        Index: pd.DatetimeIndex (sorted ascending)
        Columns: must include 'close' (float)
        Rows: at least 2

    Returns a BacktestResult with total_return = (last_close / first_close) - 1.
    """
    if prices.empty:
        raise ValueError("prices DataFrame is empty; cannot run a backtest")
    if "close" not in prices.columns:
        raise ValueError("prices DataFrame must contain a 'close' column")
    if len(prices) < 2:
        raise ValueError("need at least 2 price bars to run a backtest")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices DataFrame index must be sorted ascending")

    first_close = float(prices["close"].iloc[0])
    last_close = float(prices["close"].iloc[-1])

    if first_close <= 0:
        raise ValueError(f"first close must be positive, got {first_close}")

    # Buy as many shares as initial_capital allows at the open price.
    # Use float shares (no fractional-share rounding) to keep math exact.
    # When we add transaction costs in a later phase, we'll switch to whole shares.
    shares = initial_capital / first_close
    final_value = shares * last_close
    total_return = (final_value / initial_capital) - 1.0

    return BacktestResult(
        ticker=ticker,
        strategy_name="buy_and_hold",
        start_date=prices.index[0].date(),
        end_date=prices.index[-1].date(),
        initial_capital=initial_capital,
        final_value=final_value,
        total_return=total_return,
    )