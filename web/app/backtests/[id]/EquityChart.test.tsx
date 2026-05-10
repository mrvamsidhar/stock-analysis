import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import EquityChart from "./EquityChart";
import type { EquityPoint, PriceBar } from "@/lib/api";

// Mock the API module to bypass env-var check at import time
// (we only use types from it, not runtime values).
vi.mock("@/lib/api", () => ({}));

// Recharts uses ResizeObserver, which jsdom doesn't implement. Polyfill.
beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
  vi.spyOn(console, "warn").mockImplementation(() => {});
});

afterAll(() => {
  vi.restoreAllMocks();
});

const SAMPLE_EQUITY: EquityPoint[] = [
  { date: "2026-01-01", value: 10000 },
  { date: "2026-01-02", value: 10100 },
  { date: "2026-01-03", value: 10250 },
];

const SAMPLE_PRICES: PriceBar[] = [
  { timestamp: "2026-01-01T00:00:00Z", open: 100, high: 101, low: 99, close: 100, volume: 1_000_000 },
  { timestamp: "2026-01-02T00:00:00Z", open: 100, high: 102, low: 99, close: 101, volume: 1_100_000 },
  { timestamp: "2026-01-03T00:00:00Z", open: 101, high: 103, low: 100, close: 102.5, volume: 1_050_000 },
];

describe("EquityChart", () => {
  it("renders empty-state message when given no equity data", () => {
    render(
      <EquityChart
        equityCurve={[]}
        initialCapital={10000}
        pricesForComparison={SAMPLE_PRICES}
      />
    );
    expect(screen.getByText(/no equity data/i)).toBeInTheDocument();
  });

  it("does NOT render empty-state when given equity data", () => {
    render(
      <EquityChart
        equityCurve={SAMPLE_EQUITY}
        initialCapital={10000}
        pricesForComparison={SAMPLE_PRICES}
      />
    );
    expect(screen.queryByText(/no equity data/i)).not.toBeInTheDocument();
  });

  it("shows comparison-unavailable note when prices array is empty", () => {
    render(
      <EquityChart
        equityCurve={SAMPLE_EQUITY}
        initialCapital={10000}
        pricesForComparison={[]}
      />
    );
    expect(
      screen.getByText(/buy-and-hold comparison unavailable/i)
    ).toBeInTheDocument();
  });

  it("does NOT show comparison-unavailable note when prices are provided", () => {
    render(
      <EquityChart
        equityCurve={SAMPLE_EQUITY}
        initialCapital={10000}
        pricesForComparison={SAMPLE_PRICES}
      />
    );
    expect(
      screen.queryByText(/buy-and-hold comparison unavailable/i)
    ).not.toBeInTheDocument();
  });
});