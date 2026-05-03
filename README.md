# Stock Analysis

A self-built system for stock price ingestion, analysis, and (eventually) algorithmic paper trading.

Built phase by phase. Currently shipped: Phase 1 (price ingestion) + Phase 2 (REST API).

## Architecture
stock-analysis/
├── docker-compose.yaml    # TimescaleDB container
├── .env                   # DB credentials (not committed)
├── ingestion/             # Phase 1: pulls daily prices into TimescaleDB
└── api/                   # Phase 2: FastAPI service exposing prices over HTTP
Two databases run on the same Postgres container:
- `trading` — production data (populated by ingestion)
- `trading_test` — used by the API test suite (seeded fresh per test run)

## Stack

- TimescaleDB (PostgreSQL 16)
- Docker + Docker Compose
- Python 3.12, FastAPI, asyncpg, Pydantic v2
- pytest + pytest-asyncio + httpx for testing

## Prerequisites

- Docker Desktop (running)
- Python 3.12
- (Phase 1 only) An API key for the price data source — see `ingestion/`

## Setup

### 1. Start the database

From the project root:
docker compose up -d
docker ps
You should see `trading_db` listed.

### 2. Run Phase 1 — ingestion
cd ingestion
python -m venv venv               # first time only
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt   # first time only
python verify.py                  # confirms DB connection + recent data
To pull fresh prices, run the ingestion script (see `ingestion/` for details).

### 3. Run Phase 2 — API
cd api
python -m venv venv               # first time only
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt   # first time only
uvicorn app.main:app --reload --port 8000
The API is now live at `http://127.0.0.1:8000`.

Interactive docs: `http://127.0.0.1:8000/docs`

## API Endpoints

### `GET /health`

Returns 200 if the API and database are both reachable. Returns 503 if the DB is down.
curl http://127.0.0.1:8000/health
### `GET /stocks/{ticker}/prices`

Returns OHLCV data for a ticker between two dates (inclusive).

**Query params (both required):**
- `start` — start date, `YYYY-MM-DD`
- `end` — end date, `YYYY-MM-DD`

**Example:**
curl "http://127.0.0.1:8000/stocks/AAPL/prices?start=2026-04-01&end=2026-04-24"
**Status codes:**
- `200` — success (including empty array if no data in range)
- `400` — invalid range (start > end, or start in the future)
- `404` — unknown ticker
- `422` — malformed dates or missing parameters

## Running Tests (Phase 2 API)

The test suite runs against a separate `trading_test` database, not the production `trading` DB.

### One-time test DB setup

Connect to the Postgres container and create the test DB:

```sql
-- Connect to the trading_db container as `trader`, then run:
CREATE DATABASE trading_test OWNER trader;

-- Connect to the new trading_test database, then run:
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE prices (
    ticker TEXT NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    PRIMARY KEY (ticker, time)
);

SELECT create_hypertable('prices', 'time');
```

The test fixtures will wipe and reseed this table before each test run.

### Running the tests
cd api
.\venv\Scripts\Activate.ps1
pytest
Expected: 8 passed in under 2 seconds.

## Project Roadmap

- [x] **Phase 1** — TimescaleDB + price ingestion
- [x] **Phase 2** — FastAPI REST service
- [ ] **Phase 3** — Next.js + watchlist UI
- [ ] **Phase 4** — Stock detail + chart
- [ ] **Phase 5–6** — Backtester (vectorbt) + UI
- [ ] **Phase 7–8** — Dashboard + deployment (Hetzner + Coolify)
- [ ] **Phase 9–12** — Alpaca paper trading

## License

Private project. Not licensed for distribution.