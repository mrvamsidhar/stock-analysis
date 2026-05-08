import { describe, it, expect, beforeAll, afterAll, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import PriceChart, { type ChartPoint } from "./PriceChart";

// Recharts uses ResizeObserver, which jsdom doesn't implement.
// Polyfill it with a no-op for tests.
beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});

// Recharts also writes warnings about responsive sizing to console.warn
// when measured in jsdom. We silence them only inside this file.
beforeAll(() => {
  vi.spyOn(console, "warn").mockImplementation(() => {});
});

afterAll(() => {
  vi.restoreAllMocks();
});

describe("PriceChart", () => {
  it("renders an empty state message when given no data", () => {
    render(<PriceChart data={[]} />);
    expect(screen.getByText(/no price data/i)).toBeInTheDocument();
  });

  it("does NOT render the empty state when given data", () => {
    const data: ChartPoint[] = [
      { date: "2026-04-01", close: 100 },
      { date: "2026-04-02", close: 101 },
      { date: "2026-04-03", close: 102 },
    ];
    render(<PriceChart data={data} />);
    expect(screen.queryByText(/no price data/i)).not.toBeInTheDocument();
  });
});