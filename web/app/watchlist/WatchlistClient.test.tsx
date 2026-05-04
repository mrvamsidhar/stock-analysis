import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WatchlistClient from "./WatchlistClient";
import { fetchPrices, type PricesResponse } from "@/lib/api";

// Mock the API module entirely. fetchPrices becomes a vi.fn() we control per-test.
vi.mock("@/lib/api", () => ({
  fetchPrices: vi.fn(),
}));

const DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"];

function makeOkResponse(ticker: string): PricesResponse {
  return {
    ticker,
    count: 1,
    prices: [
      {
        timestamp: "2026-05-01T00:00:00Z",
        open: 100,
        high: 110,
        low: 99,
        close: 105,
        volume: 1_000_000,
      },
    ],
  };
}

beforeEach(() => {
  // Fresh slate before every test: empty localStorage, fresh mock.
  localStorage.clear();
  vi.mocked(fetchPrices).mockReset();
  // Default behavior: return a valid response for any ticker.
  vi.mocked(fetchPrices).mockImplementation(async (ticker) => ({
    ok: true,
    data: makeOkResponse(ticker),
  }));
});

describe("WatchlistClient", () => {
  it("renders the default 5 tickers on first load", async () => {
    render(<WatchlistClient />);

    // Each default ticker should appear in the table.
    for (const ticker of DEFAULT_TICKERS) {
      expect(await screen.findByText(ticker)).toBeInTheDocument();
    }

    // Input box should be present.
    expect(screen.getByLabelText("Add ticker")).toBeInTheDocument();
  });

  it("removes a ticker when its × button is clicked", async () => {
    const user = userEvent.setup();
    render(<WatchlistClient />);

    // Wait for AMZN to render before trying to remove it.
    await screen.findByText("AMZN");

    const removeButton = screen.getByLabelText("Remove AMZN");
    await user.click(removeButton);

    // AMZN should be gone.
    expect(screen.queryByText("AMZN")).not.toBeInTheDocument();

    // Other tickers should still be there.
    expect(screen.getByText("AAPL")).toBeInTheDocument();
  });

  it("loads tickers from localStorage if present", async () => {
    localStorage.setItem("watchlist", JSON.stringify(["TSLA", "META"]));

    render(<WatchlistClient />);

    expect(await screen.findByText("TSLA")).toBeInTheDocument();
    expect(await screen.findByText("META")).toBeInTheDocument();
    // Defaults should NOT appear.
    expect(screen.queryByText("AAPL")).not.toBeInTheDocument();
  });

  it("adds a ticker when the API returns success", async () => {
    const user = userEvent.setup();
    render(<WatchlistClient />);

    await screen.findByText("AAPL");

    const input = screen.getByLabelText("Add ticker");
    await user.type(input, "TSLA");
    await user.click(screen.getByRole("button", { name: /add/i }));

    expect(await screen.findByText("TSLA")).toBeInTheDocument();
  });

  it("shows an error and does NOT add when the API returns 404", async () => {
    const user = userEvent.setup();
    // Override the default mock for this test only.
    vi.mocked(fetchPrices).mockImplementation(async (ticker) => {
      if (ticker === "ZZZZZ") {
        return { ok: false, error: `Ticker ${ticker} not found` };
      }
      return { ok: true, data: makeOkResponse(ticker) };
    });

    render(<WatchlistClient />);
    await screen.findByText("AAPL");

    const input = screen.getByLabelText("Add ticker");
    await user.type(input, "ZZZZZ");
    await user.click(screen.getByRole("button", { name: /add/i }));

    // Error message should appear.
    expect(await screen.findByText(/not found/i)).toBeInTheDocument();
    // ZZZZZ  should NOT be in the table.
    expect(
      screen.queryByLabelText("Remove ZZZZZ")
    ).not.toBeInTheDocument();
  });
});