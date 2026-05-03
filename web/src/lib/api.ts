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