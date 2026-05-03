-- Test fixture data. Wiped and reseeded before each test run.
-- Keep this small and predictable — these exact rows back assertions in test_stocks.py.

TRUNCATE TABLE prices;

INSERT INTO prices (ticker, time, open, high, low, close, volume) VALUES
    ('AAPL', '2026-01-05 04:00:00+00', 180.0, 182.0, 179.5, 181.5, 50000000),
    ('AAPL', '2026-01-06 04:00:00+00', 181.5, 183.0, 181.0, 182.5, 48000000),
    ('AAPL', '2026-01-07 04:00:00+00', 182.5, 184.5, 182.0, 184.0, 52000000),
    ('AAPL', '2026-01-08 04:00:00+00', 184.0, 185.0, 183.0, 184.5, 47000000),
    ('AAPL', '2026-01-09 04:00:00+00', 184.5, 186.0, 184.0, 185.5, 49000000),
    ('MSFT', '2026-01-05 04:00:00+00', 410.0, 412.0, 409.0, 411.5, 25000000),
    ('MSFT', '2026-01-06 04:00:00+00', 411.5, 413.0, 410.5, 412.5, 24000000);