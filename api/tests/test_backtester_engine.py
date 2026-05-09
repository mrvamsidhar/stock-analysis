"""Tests for the backtester engine."""
import math

import pandas as pd
import pytest
import numpy as np

from app.backtester.engine import run_buy_and_hold, run_sma_crossover
from tests._lookahead_helpers import run_sma_crossover_LEAKY


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

class TestSMACrossoverHappyPath:
    """The strategy's mechanical correctness, not its profitability.

    These tests verify the engine implements SMA crossover correctly,
    NOT that the strategy makes money. Whether golden cross beats
    buy-and-hold is a market question, not an engineering one.
    """

    def test_constant_price_produces_no_trades(self):
        """If price never moves, fast and slow SMAs are equal forever.
        No crossovers should ever fire. Total return should be 0%."""
        n = 300
        prices = pd.DataFrame(
            {"close": [100.0] * n},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            prices, ticker="FLAT", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        assert result.num_trades == 0
        assert math.isclose(result.total_return, 0.0, abs_tol=1e-9)
        assert math.isclose(result.final_value, 10_000.0, rel_tol=1e-9)

    def test_single_uptrend_produces_one_buy_no_sell(self):
        """Decline-then-uptrend pattern: fast crosses above slow once.
        Strategy enters and never exits. num_trades=0, position open."""
        n = 300
        prices_array = np.concatenate([
            np.linspace(100, 90, 100),   # decline
            np.linspace(90, 130, 200),   # uptrend
        ])
        df = pd.DataFrame(
            {"close": prices_array},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            df, ticker="UP", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        # Strategy bought during uptrend, never sold (no down-cross signal).
        assert result.num_trades == 0
        # Open position at end means final_value reflects mark-to-market.
        # Should be positive return since we caught part of the uptrend.
        assert result.total_return > 0

    def test_full_cycle_produces_one_round_trip(self):
        """A clear flat-up-down-up pattern that produces buy, sell, buy.
        First crossover must be a cross-ABOVE (buy), not a cross-below.
        """
        # 100 bars at $100 to warm up both SMAs, then up->down->up.
        # By the time prices move, both SMAs are stable and tracking.
        n = 100 + 200 + 200 + 200
        prices_array = np.concatenate([
            np.full(100, 100.0),         # warmup at flat $100
            np.linspace(100, 140, 200),  # uptrend 1: triggers buy
            np.linspace(140, 80, 200),   # downtrend: triggers sell (round-trip done)
            np.linspace(80, 130, 200),   # uptrend 2: triggers buy (still open at end)
        ])
        df = pd.DataFrame(
            {"close": prices_array},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            df, ticker="CYCLE", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        # Exactly one completed round-trip: buy during uptrend1, sell during downtrend.
        # Second buy during uptrend2 stays open at end.
        assert result.num_trades == 1


class TestSMACrossoverValidation:
    """The function should reject malformed input loudly, just like buy-and-hold."""

    def test_too_few_bars_raises(self):
        n = 10  # way less than slow_window=50
        prices = pd.DataFrame(
            {"close": [100.0] * n},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        with pytest.raises(ValueError, match="at least"):
            run_sma_crossover(
                prices, ticker="X", fast_window=20, slow_window=50,
                initial_capital=10_000,
            )

    def test_fast_window_must_be_smaller_than_slow(self):
        n = 300
        prices = pd.DataFrame(
            {"close": [100.0] * n},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        with pytest.raises(ValueError, match="smaller than"):
            run_sma_crossover(
                prices, ticker="X", fast_window=50, slow_window=20,  # reversed!
                initial_capital=10_000,
            )
class TestMetricsBuyAndHold:
    """Drawdown and Sharpe on buy-and-hold equal those of the underlying stock."""

    def test_constant_price_has_zero_drawdown_and_zero_sharpe(self):
        """Flat price = flat equity = 0 drawdown, 0 Sharpe (zero variance)."""
        prices = make_prices([100.0] * 10)
        result = run_buy_and_hold(prices, ticker="FLAT", initial_capital=10_000)
        assert math.isclose(result.max_drawdown, 0.0, abs_tol=1e-9)
        assert math.isclose(result.sharpe_ratio, 0.0, abs_tol=1e-9)

    def test_drawdown_on_known_curve(self):
        """Curve [100, 110, 80, 120]: peak 110, trough 80, drawdown = 30/110 ≈ 0.2727."""
        prices = make_prices([100.0, 110.0, 80.0, 120.0])
        result = run_buy_and_hold(prices, ticker="DD", initial_capital=10_000)
        # Equity curve scales the price curve proportionally:
        # shares = 10000/100 = 100, equity = [10000, 11000, 8000, 12000]
        # peak 11000, trough 8000, drawdown = 3000/11000 = 0.27272727...
        expected_drawdown = 3000.0 / 11000.0
        assert math.isclose(result.max_drawdown, expected_drawdown, rel_tol=1e-9)

    def test_equity_curve_length_matches_input(self):
        """Equity curve has exactly one point per input bar."""
        prices = make_prices([100.0, 105.0, 110.0, 95.0, 100.0])
        result = run_buy_and_hold(prices, ticker="LEN", initial_capital=10_000)
        assert len(result.equity_curve) == 5

    def test_equity_curve_first_and_last_match_capital_and_final(self):
        """First equity point should equal initial_capital (we bought at first close).
        Last equity point should equal final_value."""
        prices = make_prices([100.0, 105.0, 110.0])
        result = run_buy_and_hold(prices, ticker="ENDS", initial_capital=10_000)
        assert math.isclose(result.equity_curve[0].value, 10_000.0, rel_tol=1e-9)
        assert math.isclose(result.equity_curve[-1].value, result.final_value, rel_tol=1e-9)

    def test_buy_and_hold_is_open_at_end(self):
        """Buy-and-hold always holds shares at end of backtest."""
        prices = make_prices([100.0, 110.0])
        result = run_buy_and_hold(prices, ticker="OPEN", initial_capital=10_000)
        assert result.is_open_at_end is True


class TestMetricsSMACrossover:
    """Equity curve, drawdown, and is_open_at_end behavior on the strategy."""

    def test_constant_price_has_flat_equity_zero_drawdown(self):
        """Constant price = no signals = strategy in cash entire time = flat equity."""
        n = 300
        prices = pd.DataFrame(
            {"close": [100.0] * n},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            prices, ticker="FLAT", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        # Strategy never traded, so equity = initial_capital throughout.
        assert math.isclose(result.max_drawdown, 0.0, abs_tol=1e-9)
        assert all(
            math.isclose(point.value, 10_000.0, rel_tol=1e-9)
            for point in result.equity_curve
        )
        assert result.is_open_at_end is False

    def test_uptrend_strategy_is_open_at_end(self):
        """Decline-then-uptrend: strategy buys, never sells. Position open at end."""
        import numpy as np
        n = 300
        prices_array = np.concatenate([
            np.linspace(100, 90, 100),
            np.linspace(90, 130, 200),
        ])
        df = pd.DataFrame(
            {"close": prices_array},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            df, ticker="UP", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        assert result.is_open_at_end is True
        assert result.num_trades == 0  # Never sold = no completed round-trips

    def test_full_cycle_closes_position_after_sell(self):
        """One full round-trip: position should be closed after the sell."""
        import numpy as np
        n = 100 + 200 + 200
        prices_array = np.concatenate([
            np.full(100, 100.0),         # warmup
            np.linspace(100, 140, 200),  # uptrend: triggers buy
            np.linspace(140, 80, 200),   # downtrend: triggers sell, ends in cash
        ])
        df = pd.DataFrame(
            {"close": prices_array},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        result = run_sma_crossover(
            df, ticker="CLOSED", fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        assert result.num_trades == 1
        assert result.is_open_at_end is False  # Sold; back in cash at end.

class TestLookAheadBiasDetection:
    """Bug-class detection: prove the clean strategy doesn't peek at today's close.

    These tests are structurally different from previous tests. Earlier tests
    assert "given input X, expect output Y." These tests assert "given the same
    input, the clean strategy must perform differently from the buggy reference
    strategy in a specific direction." If a future regression makes the clean
    strategy peek at today's data, the relationship breaks and these tests fail.
    """

    def test_clean_strategy_underperforms_leaky_on_post_crossover_jump(self):
        """The look-ahead bias detector.

        Construction:
            - 100 bars of flat warmup (both SMAs settle)
            - 200 bars of slow uptrend (drives a clean cross-above signal)
            - One sharp upward jump right after the crossover fires
            - Then a longer continuation so both strategies are in the trade
              long enough to measure the entry-price difference

        Expected:
            The buggy version sees the cross AND today's price jump on the same
            bar -- it buys cheap. The clean version, using only yesterday's SMA,
            buys ONE BAR LATER, after the price has jumped. Worse entry price
            for the clean version.

            Therefore: leaky.total_return > clean.total_return.

        If this assertion ever fails, the clean strategy has acquired a
        look-ahead bias bug (or the leaky reference has lost one). Either
        way, investigate.
        """
        import numpy as np

        warmup = np.full(100, 100.0)
        uptrend = np.linspace(100, 130, 200)
        # The "jump bar": price spikes 5% in one bar, right after warmup+uptrend
        jump = np.array([136.5])  # 130 -> 136.5 = ~5% jump in one bar
        continuation = np.linspace(136.5, 145.0, 100)

        prices_array = np.concatenate([warmup, uptrend, jump, continuation])
        n = len(prices_array)
        df = pd.DataFrame(
            {"close": prices_array},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )

        clean = run_sma_crossover(
            df, ticker="LOOKAHEAD",
            fast_window=20, slow_window=50,
            initial_capital=10_000,
        )
        leaky = run_sma_crossover_LEAKY(
            df, ticker="LOOKAHEAD",
            fast_window=20, slow_window=50,
            initial_capital=10_000,
        )

        # Both strategies must have entered at least one trade for this test
        # to be meaningful. If neither traded, the test design is wrong, not
        # the strategies.
        assert clean.is_open_at_end or clean.num_trades > 0, \
            "Clean strategy never traded; test data needs adjustment"
        assert leaky.is_open_at_end or leaky.num_trades > 0, \
            "Leaky strategy never traded; test data needs adjustment"

        # The core claim: the leaky version performs strictly better on this
        # specific construction. The gap is the magnitude of the look-ahead bug.
        assert leaky.total_return > clean.total_return, (
            f"Look-ahead bias detector failed: leaky={leaky.total_return:.4f} "
            f"is not greater than clean={clean.total_return:.4f}. "
            f"Either the clean strategy has acquired look-ahead bias, or the "
            f"leaky reference has lost it. Investigate."
        )

    def test_both_strategies_produce_zero_trades_on_constant_price(self):
        """Calibration check: the buggy reference shouldn't have UNRELATED bugs.

        On a perfectly flat price series, neither strategy should fire any
        signals -- because no crossovers can occur in a flat series.
        If the leaky version trades on flat data, it has bugs beyond just
        look-ahead bias and isn't a valid reference.
        """
        n = 300
        flat = pd.DataFrame(
            {"close": [100.0] * n},
            index=pd.date_range("2024-01-01", periods=n, freq="D"),
        )
        clean = run_sma_crossover(
            flat, ticker="FLAT",
            fast_window=20, slow_window=50, initial_capital=10_000,
        )
        leaky = run_sma_crossover_LEAKY(
            flat, ticker="FLAT",
            fast_window=20, slow_window=50, initial_capital=10_000,
        )
        assert clean.num_trades == 0
        assert leaky.num_trades == 0
        assert clean.is_open_at_end is False
        assert leaky.is_open_at_end is False