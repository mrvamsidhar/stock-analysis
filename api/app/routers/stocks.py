"""Stock data endpoints."""
from datetime import date

from fastapi import APIRouter, Query

from app.repositories import prices as prices_repo
from app.schemas import PriceBar, PricesResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{ticker}/prices", response_model=PricesResponse)
async def get_prices(
    ticker: str,
    start: date = Query(..., description="Start date (inclusive), YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), YYYY-MM-DD"),
) -> PricesResponse:
    """Fetch OHLCV data for a ticker between two dates (inclusive)."""
    rows = await prices_repo.fetch_prices(ticker, start, end)
    bars = [PriceBar(**row) for row in rows]
    return PricesResponse(
        ticker=ticker.upper(),
        count=len(bars),
        prices=bars,
    )