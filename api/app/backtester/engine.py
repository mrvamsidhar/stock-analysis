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
        the moment of the trade (look-ahead bias). The .shift(1) below is the
        single most important line in this function.

    Position sizing:
        Always all-in. When buying, use 100% of cash. When selling, sell 100%
        of position. No partial positions, no shorts, no leverage.
    """
    # ----- Input validation (same shape as buy_and_hold's checks) -----
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
        # +2 because: need slow_window bars to compute the slow SMA at all,
        # +1 more to .shift(1), and we need at least one tradeable bar after.
        raise ValueError(
            f"need at least {slow_window + 2} bars to run SMA{fast_window}/{slow_window}; "
            f"got {len(prices)}"
        )

    close = prices["close"]

    # ----- Compute indicators -----
    fast_sma = close.rolling(window=fast_window).mean()
    slow_sma = close.rolling(window=slow_window).mean()

    # ----- The critical shift: use yesterday's complete data to decide today's trade -----
    # Without .shift(1), this strategy would have look-ahead bias and produce
    # artificially good results that wouldn't happen in real trading.
    fast_prev = fast_sma.shift(1)
    slow_prev = slow_sma.shift(1)
    fast_prev_prev = fast_sma.shift(2)
    slow_prev_prev = slow_sma.shift(2)

    # A "cross above" means: yesterday fast was BELOW slow, today fast is ABOVE slow
    # (using shifted values, so "today's decision" = "yesterday's vs day-before SMA")
    cross_above = (fast_prev_prev <= slow_prev_prev) & (fast_prev > slow_prev)
    cross_below = (fast_prev_prev >= slow_prev_prev) & (fast_prev < slow_prev)

    # ----- Walk forward through bars, executing trades -----
    cash = initial_capital
    shares = 0.0
    num_trades = 0  # counts completed round-trips

    for i in range(len(prices)):
        price_today = float(close.iloc[i])
        is_buy_signal = bool(cross_above.iloc[i])
        is_sell_signal = bool(cross_below.iloc[i])

        if is_buy_signal and shares == 0:
            # Going from cash to long position
            shares = cash / price_today
            cash = 0.0
        elif is_sell_signal and shares > 0:
            # Going from long position to cash; this completes a round-trip
            cash = shares * price_today
            shares = 0.0
            num_trades += 1

    # ----- Mark to market: if still holding shares, value them at last close -----
    last_close = float(close.iloc[-1])
    final_value = cash + shares * last_close
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
    )