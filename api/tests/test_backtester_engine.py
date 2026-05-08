"""Tests for the backtester engine."""
import math

import pandas as pd
import pytest

from app.backtester.engine import run_buy_and_hold


def make_prices(closes: list[float], start: str = "2026-01-01") -> pd.DataFrame:
    """Helper: build a price DataFrame with a daily DatetimeIndex."""
    dates = pd.date_range(start, periods=len(closes), freq="D")
    return pd.DataFrame({"close": closes}, index=dates)


class TestBuyAndHoldHappyPath:
    """The math identity: total_return == (last_close / first_close) - 1.

    If buy-and-hold violates this identity, the engine itself is broken
    and no other strategy result can be trusted.
    """

    def test_simple_10_percent_gain(self):
        prices = make_prices([100.0, 102.0, 105.0, 103.0, 110.0])
        result = run_buy_and_hold(prices, ticker="TEST", initial_capital=10_000)

        assert result.ticker == "TEST"
        assert result.strategy_name == "buy_and_hold"
        assert result.initial_capital == 10_000
        assert math.isclose(result.final_value, 11_000.0, rel_tol=1e-9)
        assert math.isclose(result.total_return, 0.10, rel_tol=1e-9)

    def test_loss(self):
        prices = make_prices([100.0, 90.0, 80.0])
        result = run_buy_and_hold(prices, ticker="LOSS", initial_capital=1_000)
        # 80/100 - 1 = -0.20
        assert math.isclose(result.total_return, -0.20, rel_tol=1e-9)
        assert math.isclose(result.final_value, 800.0, rel_tol=1e-9)

    def test_flat(self):
        prices = make_prices([100.0, 105.0, 100.0])
        result = run_buy_and_hold(prices, ticker="FLAT", initial_capital=5_000)
        # First and last identical, return is exactly 0
        assert math.isclose(result.total_return, 0.0, abs_tol=1e-9)

    def test_dates_are_first_and_last_of_index(self):
        prices = make_prices([100.0, 110.0, 120.0], start="2025-06-15")
        result = run_buy_and_hold(prices, ticker="DATES", initial_capital=1_000)
        assert str(result.start_date) == "2025-06-15"
        assert str(result.end_date) == "2025-06-17"


class TestBuyAndHoldValidation:
    """The function should reject malformed input loudly."""

    def test_empty_dataframe_raises(self):
        empty = pd.DataFrame({"close": []}, index=pd.DatetimeIndex([]))
        with pytest.raises(ValueError, match="empty"):
            run_buy_and_hold(empty, ticker="X", initial_capital=1_000)

    def test_missing_close_column_raises(self):
        prices = pd.DataFrame(
            {"open": [100.0, 110.0]},
            index=pd.date_range("2026-01-01", periods=2, freq="D"),
        )
        with pytest.raises(ValueError, match="close"):
            run_buy_and_hold(prices, ticker="X", initial_capital=1_000)

    def test_single_row_raises(self):
        prices = make_prices([100.0])
        with pytest.raises(ValueError, match="at least 2"):
            run_buy_and_hold(prices, ticker="X", initial_capital=1_000)

    def test_unsorted_index_raises(self):
        # Build a DataFrame whose index is descending instead of ascending
        dates = pd.date_range("2026-01-01", periods=3, freq="D")[::-1]
        prices = pd.DataFrame({"close": [110.0, 105.0, 100.0]}, index=dates)
        with pytest.raises(ValueError, match="sorted"):
            run_buy_and_hold(prices, ticker="X", initial_capital=1_000)

    def test_zero_first_close_raises(self):
        prices = make_prices([0.0, 100.0])
        with pytest.raises(ValueError, match="positive"):
            run_buy_and_hold(prices, ticker="X", initial_capital=1_000)