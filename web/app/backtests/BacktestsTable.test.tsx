import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BacktestsTable } from "./page";
import type { BacktestRunSummary } from "@/lib/api";


vi.mock("@/lib/api", () => ({}));

const SAMPLE_RUNS: BacktestRunSummary[] = [
  {
    id: "run-1",
    ticker: "AAPL",
    strategy_name: "buy_and_hold",
    start_date: "2026-02-01",
    end_date: "2026-05-01",
    total_return: 0.0385,
    num_trades: 0,
    max_drawdown: 0.1124,
    sharpe_ratio: 0.73,
    is_open_at_end: true,
    created_at: "2026-05-10T04:03:46Z",
  },
  {
    id: "run-2",
    ticker: "MSFT",
    strategy_name: "sma_crossover",
    start_date: "2026-01-01",
    end_date: "2026-04-01",
    total_return: -0.025,
    num_trades: 2,
    max_drawdown: 0.08,
    sharpe_ratio: -0.4,
    is_open_at_end: false,
    created_at: "2026-05-09T10:00:00Z",
  },
];

describe("BacktestsTable", () => {
  it("renders one row per backtest run", () => {
    render(<BacktestsTable runs={SAMPLE_RUNS} />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("buy_and_hold")).toBeInTheDocument();
    expect(screen.getByText("sma_crossover")).toBeInTheDocument();
  });

  it("links each ticker to its detail page", () => {
    render(<BacktestsTable runs={SAMPLE_RUNS} />);
    const aaplLink = screen.getByRole("link", { name: "AAPL" });
    const msftLink = screen.getByRole("link", { name: "MSFT" });
    expect(aaplLink).toHaveAttribute("href", "/backtests/run-1");
    expect(msftLink).toHaveAttribute("href", "/backtests/run-2");
  });

  it("formats positive returns with a + sign", () => {
    render(<BacktestsTable runs={SAMPLE_RUNS} />);
    expect(screen.getByText("+3.85%")).toBeInTheDocument();
  });

  it("formats negative returns without an extra sign", () => {
    render(<BacktestsTable runs={SAMPLE_RUNS} />);
    // -0.025 -> -2.50%, no additional + prefix
    expect(screen.getByText("-2.50%")).toBeInTheDocument();
  });

  it("shows drawdown as a positive magnitude with a leading minus", () => {
    render(<BacktestsTable runs={SAMPLE_RUNS} />);
    // Both runs have non-zero drawdown rendered with a minus prefix.
    expect(screen.getByText("−11.24%")).toBeInTheDocument();
    expect(screen.getByText("−8.00%")).toBeInTheDocument();
  });
});