"""
fetch_prices.py
Pulls 1 year of daily price data for 5 tickers from Yahoo Finance
and inserts it into the TimescaleDB 'prices' table.
"""

import os
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load DB credentials from .env file into environment variables
load_dotenv()

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]


def get_db_connection():
    """Open a connection to the TimescaleDB database."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def fetch_ticker_data(ticker: str):
    """Fetch ~1 year of daily OHLCV bars for a single ticker."""
    print(f"Fetching {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y", interval="1d")

    if df.empty:
        print(f"  No data returned for {ticker}")
        return []

    # Convert pandas DataFrame to a list of tuples for SQL insert
    rows = []
    for time_idx, row in df.iterrows():
        rows.append((
            ticker,
            time_idx.to_pydatetime(),
            float(row["Open"]),
            float(row["High"]),
            float(row["Low"]),
            float(row["Close"]),
            int(row["Volume"]),
        ))

    print(f"  Got {len(rows)} bars")
    return rows


def insert_prices(conn, rows):
    """Bulk-insert price rows. Skip duplicates via ON CONFLICT."""
    if not rows:
        return

    sql = """
        INSERT INTO prices (ticker, time, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (ticker, time) DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()


def main():
    conn = get_db_connection()
    try:
        for ticker in TICKERS:
            rows = fetch_ticker_data(ticker)
            insert_prices(conn, rows)
        print("\n✅ Done. All tickers loaded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()