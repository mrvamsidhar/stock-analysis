"""Backtester engine.

Why this file exists:
- Pure functions that take price data + strategy params, return BacktestResult.
- No DB access, no I/O, no globals. The function signature is the contract.
- Testability + composability over cleverness.
"""
import pandas as pd

from app.backtester.metrics import compute_max_drawdown, compute_sharpe_ratio
from app.backtester.schemas import BacktestResult, EquityPoint


def _equity_curve_to_points(equity: pd.Series) -> list[EquityPoint]:
    """Convert an equity Series (DatetimeIndex) into a list of EquityPoint models."""
    return [
        EquityPoint(date=ts.date(), value=float(value))
        for ts, value in equity.items()
    ]


def run_buy_and_hold(
    prices: pd.DataFrame,
    ticker: str,
    initial_capital: float = 10_000.0,
) -> BacktestResult:
    """Buy on the first day, hold to the last day, sell on the last day.

    Buy-and-hold is the control case. Every other strategy must beat this
    to be worth implementing. It's also the unit test for the engine itself --
    if buy-and-hold is wrong, all other strategies are wrong.

    Expected DataFrame shape:
        Index: pd.DatetimeIndex (sorted ascending)
        Columns: must include 'close' (float)
        Rows: at least 2

    Returns a BacktestResult with full metrics (equity_curve, max_drawdown, etc.).
    """
    if prices.empty:
        raise ValueError("prices DataFrame is empty; cannot run a backtest")
    if "close" not in prices.columns:
        raise ValueError("prices DataFrame must contain a 'close' column")
    if len(prices) < 2:
        raise ValueError("need at least 2 price bars to run a backtest")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices DataFrame index must be sorted ascending")

    close = prices["close"]
    first_close = float(close.iloc[0])

    if first_close <= 0:
        raise ValueError(f"first close must be positive, got {first_close}")

    # Buy as many shares as initial_capital allows at the first close.
    shares = initial_capital / first_close

    # Equity at each bar = shares held * close on that bar.
    # Buy-and-hold holds shares the entire backtest, so equity tracks price.
    equity = shares * close

    final_value = float(equity.iloc[-1])
    total_return = (final_value / initial_capital) - 1.0

    return BacktestResult(
        ticker=ticker,
        strategy_name="buy_and_hold",
        start_date=prices.index[0].date(),
        end_date=prices.index[-1].date(),
        initial_capital=initial_capital,
        final_value=final_value,
        total_return=total_return,
        num_trades=0,  # Buy-and-hold never closes a round-trip.
        max_drawdown=compute_max_drawdown(equity),
        sharpe_ratio=compute_sharpe_ratio(equity),
        equity_curve=_equity_curve_to_points(equity),
        is_open_at_end=True,  # Always holds shares through to the end.
    )


def run_sma_crossover(
    prices: pd.DataFrame,
    ticker: str,
    fast_window: int = 50,
    slow_window: int = 200,
    initial_capital: float = 10_000.0,
) -> BacktestResult:
    """SMA crossover strategy: buy when fast SMA crosses above slow SMA.

    Signals:
        BUY  when fast_sma crosses above slow_sma (going from below to above)
        SELL when fast_sma crosses below slow_sma (going from above to below)

    Trade execution:
        Trades execute at the close price on the day the signal fires. We use
        YESTERDAY's SMA values to decide TODAY's trade -- without this shift,
        the backtest secretly uses information that wasn't yet available at
        the moment of the trade (look-ahead bias). The .shift() lines below
        are the single most important code in this function.

    Position sizing:
        Always all-in. When buying, use 100% of cash. When selling, sell 100%
        of position. No partial positions, no shorts, no leverage.
    """
    if prices.empty:
        raise ValueError("prices DataFrame is empty; cannot run a backtest")
    if "close" not in prices.columns:
        raise ValueError("prices DataFrame must contain a 'close' column")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices DataFrame index must be sorted ascending")
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("fast_window and slow_window must be positive")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    if len(prices) < slow_window + 2:
        raise ValueError(
            f"need at least {slow_window + 2} bars to run SMA{fast_window}/{slow_window}; "
            f"got {len(prices)}"
        )

    close = prices["close"]

    fast_sma = close.rolling(window=fast_window).mean()
    slow_sma = close.rolling(window=slow_window).mean()

    fast_prev = fast_sma.shift(1)
    slow_prev = slow_sma.shift(1)
    fast_prev_prev = fast_sma.shift(2)
    slow_prev_prev = slow_sma.shift(2)

    cross_above = (fast_prev_prev <= slow_prev_prev) & (fast_prev > slow_prev)
    cross_below = (fast_prev_prev >= slow_prev_prev) & (fast_prev < slow_prev)

    cash = initial_capital
    shares = 0.0
    num_trades = 0
    equity_values: list[float] = []  # one per bar, in order

    for i in range(len(prices)):
        price_today = float(close.iloc[i])
        is_buy_signal = bool(cross_above.iloc[i])
        is_sell_signal = bool(cross_below.iloc[i])

        if is_buy_signal and shares == 0:
            shares = cash / price_today
            cash = 0.0
        elif is_sell_signal and shares > 0:
            cash = shares * price_today
            shares = 0.0
            num_trades += 1

        # Record portfolio value at end of this bar.
        equity_values.append(cash + shares * price_today)

    equity = pd.Series(equity_values, index=prices.index)
    final_value = float(equity.iloc[-1])
    total_return = (final_value / initial_capital) - 1.0

    return BacktestResult(
        ticker=ticker,
        strategy_name="sma_crossover",
        start_date=prices.index[0].date(),
        end_date=prices.index[-1].date(),
        initial_capital=initial_capital,
        final_value=final_value,
        total_return=total_return,
        num_trades=num_trades,
        max_drawdown=compute_max_drawdown(equity),
        sharpe_ratio=compute_sharpe_ratio(equity),
        equity_curve=_equity_curve_to_points(equity),
        is_open_at_end=shares > 0,
    )

# Strategy registry: maps strategy_name -> engine function.
# Adding a new strategy is one line here. Routers and tests look up
# strategies through this dictionary, so they don't need to change.
STRATEGY_REGISTRY = {
    "buy_and_hold": run_buy_and_hold,
    "sma_crossover": run_sma_crossover,
}