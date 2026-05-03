/**
 * Typed client for the Stock Analysis API.
 *
 * Why this file exists:
 * - Centralizes all fetches to our FastAPI service.
 * - Defines TypeScript types matching the server's response shapes.
 * - When the API changes, only this file needs to update — pages don't
 *   know or care about the wire format.
 */

const API_BASE_URL = process.env.API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error(
    "API_BASE_URL is not set. Copy .env.example to .env.local."
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