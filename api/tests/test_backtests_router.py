"""Integration tests for /backtests endpoints.

Tests use the same async client fixture as test_stocks.py.
asyncio_mode=auto in pytest.ini handles the async machinery automatically.
"""
from uuid import uuid4

# Date range determined by what's in trading_test seed data.
# DO NOT change without updating seed_data.sql.
SEED_TICKER = "AAPL"
SEED_START = "2026-01-05"
SEED_END = "2026-01-09"


async def test_post_run_buy_and_hold_happy_path(client):
    """Run a buy-and-hold backtest. Should persist and return 201 with full result."""
    response = await client.post(
        "/backtests/run",
        json={
            "ticker": SEED_TICKER,
            "strategy_name": "buy_and_hold",
            "start_date": SEED_START,
            "end_date": SEED_END,
            "initial_capital": 10000,
        },
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert "id" in body
    assert body["result"]["ticker"] == SEED_TICKER
    assert body["result"]["strategy_name"] == "buy_and_hold"
    assert body["result"]["initial_capital"] == 10000
    assert "total_return" in body["result"]
    assert len(body["result"]["equity_curve"]) >= 2


async def test_post_run_unknown_strategy_returns_400(client):
    response = await client.post(
        "/backtests/run",
        json={
            "ticker": SEED_TICKER,
            "strategy_name": "voodoo_strategy",
            "start_date": SEED_START,
            "end_date": SEED_END,
        },
    )
    assert response.status_code == 400
    assert "Unknown strategy" in response.json()["detail"]


async def test_post_run_unknown_ticker_returns_404(client):
    response = await client.post(
        "/backtests/run",
        json={
            "ticker": "FAKEXYZ",
            "strategy_name": "buy_and_hold",
            "start_date": SEED_START,
            "end_date": SEED_END,
        },
    )
    assert response.status_code == 404
    assert "Unknown ticker" in response.json()["detail"]


async def test_post_run_start_after_end_returns_400(client):
    response = await client.post(
        "/backtests/run",
        json={
            "ticker": SEED_TICKER,
            "strategy_name": "buy_and_hold",
            "start_date": SEED_END,
            "end_date": SEED_START,  # reversed
        },
    )
    assert response.status_code == 400


async def test_get_after_post_returns_same_run(client):
    """Round-trip: create a run, then fetch it by id."""
    post_response = await client.post(
        "/backtests/run",
        json={
            "ticker": SEED_TICKER,
            "strategy_name": "buy_and_hold",
            "start_date": SEED_START,
            "end_date": SEED_END,
            "initial_capital": 10000,
        },
    )
    assert post_response.status_code == 201
    run_id = post_response.json()["id"]

    get_response = await client.get(f"/backtests/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == run_id
    assert get_response.json()["result"]["ticker"] == SEED_TICKER


async def test_get_unknown_id_returns_404(client):
    random_id = str(uuid4())
    response = await client.get(f"/backtests/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


async def test_list_includes_recent_runs(client):
    """The list endpoint should include any run we just inserted, in summary form."""
    post_response = await client.post(
        "/backtests/run",
        json={
            "ticker": SEED_TICKER,
            "strategy_name": "buy_and_hold",
            "start_date": SEED_START,
            "end_date": SEED_END,
            "initial_capital": 10000,
        },
    )
    assert post_response.status_code == 201
    new_id = post_response.json()["id"]

    list_response = await client.get("/backtests")
    assert list_response.status_code == 200
    runs = list_response.json()
    ids = [run["id"] for run in runs]
    assert new_id in ids

    # Summary view: equity_curve must NOT be present
    for run in runs:
        assert "equity_curve" not in run
        assert "total_return" in run