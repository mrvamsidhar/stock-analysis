-- Migration 001: Create backtest_runs table.
--
-- Purpose: Persist backtest results so they can be re-fetched without
-- re-running. Each row is one execution of one strategy on one ticker
-- over one date range.
--
-- Idempotency: This script can be run multiple times safely (CREATE
-- EXTENSION IF NOT EXISTS, CREATE TABLE IF NOT EXISTS).
--
-- Apply to both `trading` and `trading_test` databases.

-- pgcrypto provides gen_random_uuid().
-- TimescaleDB images usually have it preinstalled, but be explicit.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS backtest_runs (
    id              UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker          TEXT                     NOT NULL,
    strategy_name   TEXT                     NOT NULL,
    strategy_params JSONB                    NOT NULL,
    start_date      DATE                     NOT NULL,
    end_date        DATE                     NOT NULL,
    initial_capital DOUBLE PRECISION         NOT NULL,
    final_value     DOUBLE PRECISION         NOT NULL,
    total_return    DOUBLE PRECISION         NOT NULL,
    num_trades      INTEGER                  NOT NULL DEFAULT 0,
    max_drawdown    DOUBLE PRECISION         NOT NULL DEFAULT 0,
    sharpe_ratio    DOUBLE PRECISION         NOT NULL DEFAULT 0,
    is_open_at_end  BOOLEAN                  NOT NULL DEFAULT FALSE,
    equity_curve    JSONB                    NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ              NOT NULL DEFAULT NOW()
);

-- Most common query in the API will be "show this user's recent backtests
-- for this ticker." Index supports that pattern.
CREATE INDEX IF NOT EXISTS idx_backtest_runs_ticker_created
    ON backtest_runs (ticker, created_at DESC);