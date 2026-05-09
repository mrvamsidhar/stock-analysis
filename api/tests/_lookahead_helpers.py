"""Test-only helpers for look-ahead bias detection.

Why this file exists:
- Look-ahead bias detection requires a deliberately buggy "reference" strategy
  to compare against the real one. That buggy strategy must NEVER be importable
  from production code (app/), only from tests.
- The leading underscore in the filename is a convention to signal "internal
  test fixture, not a real test module."

DO NOT import any of these from app/ code. They exist only to prove that our
real strategies do NOT have the kinds of bugs they deliberately implement.
"""
import pandas as pd

from app.backtester.metrics import compute_max_drawdown, compute_sharpe_ratio
from app.backtester.schemas import BacktestResult, EquityPoint


def _equity_to_points(equity: pd.Series) -> list[EquityPoint]:
    """Same shape as engine._equity_curve_to_points, duplicated here to keep
    the helper file self-contained."""
    return [
        EquityPoint(date=ts.date(), value=float(value))
        for ts, value in equity.items()
    ]


def run_sma_crossover_LEAKY(
    prices: pd.DataFrame,
    ticker: str,
    fast_window: int = 50,
    slow_window: int = 200,
    initial_capital: float = 10_000.0,
) -> BacktestResult:
    """DELIBERATELY BUGGY: SMA crossover that uses TODAY's data for TODAY's trade.

    This is the look-ahead bias bug we're trying to detect in production code.
    The function is identical to run_sma_crossover EXCEPT that it omits the
    .shift(1) calls -- the single most important lines in the real strategy.

    Expected behavior on synthetic data:
        Returns artificially BETTER than the clean version, because the strategy
        sees today's complete close and reacts to crossings on the same bar
        instead of one bar later.

    DO NOT EVER use this in production. It's here to fail loudly in tests
    so we can prove the clean version doesn't have this bug.
    """
    if len(prices) < slow_window + 2:
        raise ValueError(f"need at least {slow_window + 2} bars; got {len(prices)}")

    close = prices["close"]
    fast_sma = close.rolling(window=fast_window).mean()
    slow_sma = close.rolling(window=slow_window).mean()

    # ---- THE BUG ----
    # No .shift() here. We compare today's SMA values directly, which means
    # the strategy "sees" today's complete close in the rolling mean and acts
    # on the same bar. Real trader couldn't have known this at trade time.
    cross_above = (fast_sma.shift(1) <= slow_sma.shift(1)) & (fast_sma > slow_sma)
    cross_below = (fast_sma.shift(1) >= slow_sma.shift(1)) & (fast_sma < slow_sma)
    # ---- END BUG ----

    cash = initial_capital
    shares = 0.0
    num_trades = 0
    equity_values: list[float] = []

    for i in range(len(prices)):
        price_today = float(close.iloc[i])
        is_buy = bool(cross_above.iloc[i])
        is_sell = bool(cross_below.iloc[i])

        if is_buy and shares == 0:
            shares = cash / price_today
            cash = 0.0
        elif is_sell and shares > 0:
            cash = shares * price_today
            shares = 0.0
            num_trades += 1

        equity_values.append(cash + shares * price_today)

    equity = pd.Series(equity_values, index=prices.index)
    final_value = float(equity.iloc[-1])
    total_return = (final_value / initial_capital) - 1.0

    return BacktestResult(
        ticker=ticker,
        strategy_name="sma_crossover_LEAKY",
        start_date=prices.index[0].date(),
        end_date=prices.index[-1].date(),
        initial_capital=initial_capital,
        final_value=final_value,
        total_return=total_return,
        num_trades=num_trades,
        max_drawdown=compute_max_drawdown(equity),
        sharpe_ratio=compute_sharpe_ratio(equity),
        equity_curve=_equity_to_points(equity),
        is_open_at_end=shares > 0,
    )