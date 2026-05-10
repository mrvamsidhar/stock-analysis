/**
 * Typed client for the Stock Analysis API.
 *
 * Why this file exists:
 * - Centralizes all fetches to our FastAPI service.
 * - Defines TypeScript types matching the server's response shapes.
 * - When the API changes, only this file needs to update — pages don't
 *   know or care about the wire format.
 */

// Server-side reads API_BASE_URL; client-side reads NEXT_PUBLIC_API_BASE_URL.
// At runtime, only one of these is defined depending on where the code runs.
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error(
    "API base URL is not set. Copy .env.example to .env.local."
  );
}

// ---------- Response types (mirror the FastAPI Pydantic models) ----------

export type HealthResponse = {
  status: "ok" | "degraded";
  database: "reachable" | "unreachable";
  error?: string;
};

// ---------- API client functions ----------

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    // Don't cache health checks — we want the live state every time.
    cache: "no-store",
  });

  if (!res.ok && res.status !== 503) {
    // 200 (healthy) and 503 (degraded) are both expected from /health.
    // Anything else is a real failure to even reach the API.
    throw new Error(`Health check failed: HTTP ${res.status}`);
  }

  return (await res.json()) as HealthResponse;
}

// ---------- Prices ----------

export type PriceBar = {
    timestamp: string;
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    volume: number | null;
  };
  
  export type PricesResponse = {
    ticker: string;
    count: number;
    prices: PriceBar[];
  };
  
  export type PricesResult =
    | { ok: true; data: PricesResponse }
    | { ok: false; error: string };
  
  /**
   * Fetch prices for a single ticker. Returns a tagged result so callers
   * can distinguish "the API was reached but said 404" from "couldn't even
   * reach the API." Caller decides how to render each case.
   */
  export async function fetchPrices(
    ticker: string,
    start: string,
    end: string
  ): Promise<PricesResult> {
    try {
      const url = `${API_BASE_URL}/stocks/${encodeURIComponent(
        ticker
      )}/prices?start=${start}&end=${end}`;
      const res = await fetch(url, { cache: "no-store" });
  
      if (res.status === 404) {
        return { ok: false, error: `Ticker ${ticker} not found` };
      }
      if (!res.ok) {
        return { ok: false, error: `HTTP ${res.status}` };
      }
  
      const data = (await res.json()) as PricesResponse;
      return { ok: true, data };
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      return { ok: false, error: msg };
    }
  }

// ============================================================
// Backtester types — match the Pydantic schemas in api/app/backtester/schemas.py.
// If those change, update here too. (TODO: replace with openapi-typescript later.)
// ============================================================

export type EquityPoint = {
  date: string;  // YYYY-MM-DD
  value: number;
};

export type BacktestResult = {
  ticker: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  num_trades: number;
  max_drawdown: number;
  sharpe_ratio: number;
  equity_curve: EquityPoint[];
  is_open_at_end: boolean;
};

export type BacktestRun = {
  id: string;
  strategy_params: Record<string, unknown>;
  result: BacktestResult;
  created_at: string;  // ISO datetime
};

export type BacktestRunSummary = {
  id: string;
  ticker: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_return: number;
  num_trades: number;
  max_drawdown: number;
  sharpe_ratio: number;
  is_open_at_end: boolean;
  created_at: string;
};

export type BacktestRequest = {
  ticker: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  strategy_params?: Record<string, unknown>;
};

// Discriminated unions for each fetcher's return shape.
// Match the pattern of PricesResult: callers handle ok/error cleanly.
export type RunBacktestResult =
  | { ok: true; data: BacktestRun }
  | { ok: false; status: number; message: string };

export type FetchBacktestResult =
  | { ok: true; data: BacktestRun }
  | { ok: false; status: number; message: string };

export type FetchBacktestsResult =
  | { ok: true; data: BacktestRunSummary[] }
  | { ok: false; status: number; message: string };

// ============================================================
// Backtester API functions
// ============================================================

export async function runBacktest(
  request: BacktestRequest
): Promise<RunBacktestResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/backtests/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      return {
        ok: false,
        status: response.status,
        message: body.detail || response.statusText,
      };
    }

    const data: BacktestRun = await response.json();
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      message: err instanceof Error ? err.message : "Network error",
    };
  }
}

export async function fetchBacktest(id: string): Promise<FetchBacktestResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/backtests/${id}`);

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      return {
        ok: false,
        status: response.status,
        message: body.detail || response.statusText,
      };
    }

    const data: BacktestRun = await response.json();
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      message: err instanceof Error ? err.message : "Network error",
    };
  }
}

export async function fetchBacktests(
  limit: number = 50
): Promise<FetchBacktestsResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/backtests?limit=${limit}`);

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      return {
        ok: false,
        status: response.status,
        message: body.detail || response.statusText,
      };
    }

    const data: BacktestRunSummary[] = await response.json();
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      message: err instanceof Error ? err.message : "Network error",
    };
  }
}