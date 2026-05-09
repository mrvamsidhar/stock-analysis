"""Pure functions for computing backtest metrics from an equity curve.

Why this file exists:
- Metrics are independent of strategy logic. Same curve in -> same metrics out.
- Splitting them from engine.py makes both files smaller and the boundaries
  cleaner. Each function does one thing, testable in isolation.
- All inputs are pandas Series; no DB, no I/O, no globals. Pure functions.
"""
import math

import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def compute_max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough decline in the equity curve, as a positive magnitude.

    Algorithm:
      1. Running maximum of equity at each point = the "high water mark"
      2. Drawdown at each point = (high_water - equity) / high_water
      3. Return the maximum of those drawdowns

    Examples:
        Curve [100, 110, 80, 120] -> peak at 110, trough at 80, drawdown = (110-80)/110 ≈ 0.273
        Curve [100, 100, 100]     -> never declined, drawdown = 0.0
        Curve [100, 90,  85]      -> peak at 100, trough at 85, drawdown = 0.15
    """
    if equity.empty:
        return 0.0

    high_water_mark = equity.cummax()
    drawdowns = (high_water_mark - equity) / high_water_mark
    return float(drawdowns.max())


def compute_sharpe_ratio(equity: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio: (mean_excess_return / std_return) * sqrt(252).

    Computed from daily returns derived from the equity curve.
    Uses risk_free_rate=0 by default (Phase 5 convention).

    Returns 0.0 when returns have no variance (constant equity curve).
    Returns 0.0 when there are <2 data points.
    """
    if len(equity) < 2:
        return 0.0

    daily_returns = equity.pct_change().dropna()
    if daily_returns.empty or daily_returns.std() == 0:
        return 0.0

    excess_returns = daily_returns - (risk_free_rate / TRADING_DAYS_PER_YEAR)
    daily_sharpe = excess_returns.mean() / daily_returns.std()
    return float(daily_sharpe * math.sqrt(TRADING_DAYS_PER_YEAR))