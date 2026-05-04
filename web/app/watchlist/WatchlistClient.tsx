"use client";

import { useEffect, useState } from "react";
import { fetchPrices, type PricesResult } from "@/lib/api";

const INITIAL_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"];

const TICKER_FORMAT = /^[A-Z]{1,5}$/;

function dateRange(): { start: string; end: string } {
  const today = new Date();
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(today.getDate() - 7);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(sevenDaysAgo), end: fmt(today) };
}

type RowState = {
  ticker: string;
  result: PricesResult | "loading";
};

type AddState =
  | { kind: "idle" }
  | { kind: "checking"; ticker: string }
  | { kind: "error"; message: string };

export default function WatchlistClient() {
  const [tickers, setTickers] = useState<string[]>(INITIAL_TICKERS);
  const [rows, setRows] = useState<RowState[]>([]);
  const [input, setInput] = useState("");
  const [addState, setAddState] = useState<AddState>({ kind: "idle" });

  // Load saved watchlist from localStorage on first mount (client-only).
  useEffect(() => {
    try {
      const stored = localStorage.getItem("watchlist");
      if (!stored) return;
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.every((t) => typeof t === "string")) {
        setTickers(parsed);
      }
    } catch {
      // Corrupted storage — fall back to defaults.
    }
  }, []);

  // Persist tickers to localStorage whenever the list changes.
  useEffect(() => {
    localStorage.setItem("watchlist", JSON.stringify(tickers));
  }, [tickers]);

  // Refetch prices whenever the ticker list changes.
  useEffect(() => {
    let cancelled = false;
    const { start, end } = dateRange();

    setRows(tickers.map((ticker) => ({ ticker, result: "loading" })));

    Promise.all(
      tickers.map(async (ticker) => ({
        ticker,
        result: await fetchPrices(ticker, start, end),
      }))
    ).then((results) => {
      if (!cancelled) setRows(results);
    });

    return () => {
      cancelled = true;
    };
  }, [tickers]);

  function handleRemove(ticker: string) {
    setTickers((prev) => prev.filter((t) => t !== ticker));
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const ticker = input.trim().toUpperCase();

    if (!TICKER_FORMAT.test(ticker)) {
      setAddState({ kind: "error", message: "Ticker must be 1-5 letters." });
      return;
    }

    if (tickers.includes(ticker)) {
      setAddState({
        kind: "error",
        message: `${ticker} is already in your watchlist.`,
      });
      return;
    }

    setAddState({ kind: "checking", ticker });
    const { start, end } = dateRange();
    const result = await fetchPrices(ticker, start, end);

    if (!result.ok) {
      setAddState({ kind: "error", message: result.error });
      return;
    }

    setTickers((prev) => [...prev, ticker]);
    setInput("");
    setAddState({ kind: "idle" });
  }

  function clearError() {
    if (addState.kind === "error") setAddState({ kind: "idle" });
  }

  return (
    <>
      <form onSubmit={handleAdd} className="mb-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            clearError();
          }}
          placeholder="Add ticker (e.g. TSLA)"
          className="flex-1 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={addState.kind === "checking"}
          aria-label="Add ticker"
        />
        <button
          type="submit"
          disabled={addState.kind === "checking" || input.trim() === ""}
          className="px-4 py-2 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {addState.kind === "checking" ? "Checking..." : "Add"}
        </button>
      </form>

      {addState.kind === "error" && (
        <div className="mb-4 px-3 py-2 rounded-md bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 text-sm">
          {addState.message}
        </div>
      )}

      <div className="rounded-lg border border-gray-300 dark:border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-semibold">
                Ticker
              </th>
              <th className="text-right px-4 py-3 text-sm font-semibold">
                Latest Close
              </th>
              <th className="text-right px-4 py-3 text-sm font-semibold">
                As of
              </th>
              <th className="px-4 py-3 text-sm font-semibold w-12"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <WatchlistRow
                key={row.ticker}
                row={row}
                onRemove={() => handleRemove(row.ticker)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function WatchlistRow({
  row,
  onRemove,
}: {
  row: RowState;
  onRemove: () => void;
}) {
  const { ticker, result } = row;

  const removeButton = (
    <td className="px-4 py-3 text-right">
      <button
        onClick={onRemove}
        className="text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
        aria-label={`Remove ${ticker}`}
      >
        ×
      </button>
    </td>
  );

  if (result === "loading") {
    return (
      <tr className="border-t border-gray-200 dark:border-gray-800">
        <td className="px-4 py-3 font-mono font-medium">{ticker}</td>
        <td className="px-4 py-3 text-right text-gray-400" colSpan={2}>
          loading...
        </td>
        {removeButton}
      </tr>
    );
  }

  if (!result.ok) {
    return (
      <tr className="border-t border-gray-200 dark:border-gray-800">
        <td className="px-4 py-3 font-mono font-medium">{ticker}</td>
        <td
          className="px-4 py-3 text-right text-red-600 dark:text-red-400"
          colSpan={2}
        >
          {result.error}
        </td>
        {removeButton}
      </tr>
    );
  }

  if (result.data.count === 0) {
    return (
      <tr className="border-t border-gray-200 dark:border-gray-800">
        <td className="px-4 py-3 font-mono font-medium">{ticker}</td>
        <td className="px-4 py-3 text-right text-gray-500" colSpan={2}>
          no recent data
        </td>
        {removeButton}
      </tr>
    );
  }

  const bars = result.data.prices;
  const latest = bars[bars.length - 1];
  const closeStr = latest.close !== null ? `$${latest.close.toFixed(2)}` : "-";
  const dateStr = latest.timestamp.slice(0, 10);

  return (
    <tr className="border-t border-gray-200 dark:border-gray-800">
      <td className="px-4 py-3 font-mono font-medium">{ticker}</td>
      <td className="px-4 py-3 text-right tabular-nums">{closeStr}</td>
      <td className="px-4 py-3 text-right text-gray-500 tabular-nums">
        {dateStr}
      </td>
      {removeButton}
    </tr>
  );
}