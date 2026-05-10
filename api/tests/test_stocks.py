"""Tests for /stocks/{ticker}/prices.

Mirrors the six manual tests we ran in Checkpoint C — but automated and
running against deterministic seed data, so results don't drift over time.
"""


async def test_happy_path_returns_aapl_prices_in_range(client):
    """Seed has 5 AAPL rows from Jan 5-9 2026. Asking for that exact range
    should return all 5."""
    response = await client.get(
        "/stocks/AAPL/prices",
        params={"start": "2026-01-05", "end": "2026-01-09"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["count"] == 5
    assert len(body["prices"]) == 5
    # Confirm we got the right shape — keys we promised in the API contract
    first = body["prices"][0]
    assert "timestamp" in first
    assert "open" in first
    assert "close" in first
    assert "volume" in first


async def test_unknown_ticker_returns_404(client):
    response = await client.get(
        "/stocks/FAKEXYZ/prices",
        params={"start": "2026-01-05", "end": "2026-01-09"},
    )
    assert response.status_code == 404
    assert "FAKEXYZ" in response.json()["detail"]


async def test_start_after_end_returns_400(client):
    response = await client.get(
        "/stocks/AAPL/prices",
        params={"start": "2026-01-09", "end": "2026-01-05"},
    )
    assert response.status_code == 400
    assert "must be on or before" in response.json()["detail"]


async def test_future_start_date_returns_400(client):
    response = await client.get(
        "/stocks/AAPL/prices",
        params={"start": "2099-01-01", "end": "2099-12-31"},
    )
    assert response.status_code == 400
    assert "future" in response.json()["detail"].lower()


async def test_valid_ticker_with_no_data_in_range_returns_empty(client):
    """AAPL exists but no rows in February 2026. Should be 200 with count:0,
    NOT a 404. This distinguishes 'unknown ticker' from 'no data in range'."""
    response = await client.get(
        "/stocks/AAPL/prices",
        params={"start": "2026-02-01", "end": "2026-02-28"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["count"] == 0
    assert body["prices"] == []


async def test_lowercase_ticker_is_normalized_to_uppercase(client):
    response = await client.get(
        "/stocks/aapl/prices",
        params={"start": "2026-01-05", "end": "2026-01-09"},
    )
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"

async def test_list_tickers_returns_seeded_tickers(client):
    """Seed has AAPL and MSFT. The endpoint should return both alphabetically."""
    response = await client.get("/tickers")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert "AAPL" in body
    assert "MSFT" in body
    # Sorted ascending
    assert body == sorted(body)