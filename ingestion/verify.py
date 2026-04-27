"""
verify.py
Health check: prints the latest close price for each ticker in the database.
Run this anytime to confirm the data pipeline is working.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    sql = """
        SELECT DISTINCT ON (ticker)
            ticker, time, close
        FROM prices
        ORDER BY ticker, time DESC;
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    print("\n📈 Latest prices in database:\n")
    print(f"{'TICKER':<8} {'DATE':<12} {'CLOSE':>10}")
    print("-" * 32)
    for ticker, time, close in rows:
        print(f"{ticker:<8} {time.date()!s:<12} ${close:>9.2f}")
    print(f"\n✅ {len(rows)} tickers verified.\n")

    conn.close()


if __name__ == "__main__":
    main()