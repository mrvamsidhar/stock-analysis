"""Stock data endpoints."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.repositories import prices as prices_repo
from app.schemas import PriceBar, PricesResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{ticker}/prices", response_model=PricesResponse)
async def get_prices(
    ticker: str,
    start: date = Query(..., description="Start date (inclusive), YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), YYYY-MM-DD"),
) -> PricesResponse:
    """Fetch OHLCV data for a ticker between two dates (inclusive).
    Errors:
    - 400 if start > end, or if start is in the future.
    - 404 if the ticker is unknown (no rows for it in the database).
    - 422 (auto from FastAPI) if dates are malformed or missing.
    Returns 200 with an empty `prices` list if the ticker is valid but
    no data exists in the requested range. That is not an error.
    """
    # 1. Validate the date range itself before touching the DB.
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"start ({start}) must be on or before end ({end}).",
        )

    today = datetime.now(timezone.utc).date()
    if start > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"start ({start}) is in the future; no data available.",
        )

    # 2. Verify the ticker exists at all. Distinguishes "unknown ticker"
    #    (404) from "valid ticker, no data in range" (200 with []).
    if not await prices_repo.ticker_exists(ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{ticker.upper()}' not found.",
        )

    # 3. Happy path: fetch and return.
    rows = await prices_repo.fetch_prices(ticker, start, end)
    bars = [PriceBar(**row) for row in rows]
    return PricesResponse(
        ticker=ticker.upper(),
        count=len(bars),
        prices=bars,
    )