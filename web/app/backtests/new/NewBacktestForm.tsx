"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { runBacktest } from "@/lib/api";

type Props = {
  tickers: string[];
};

// Sensible default date range: 90 days ending today.
function defaultDateRange(): { start: string; end: string } {
  const today = new Date();
  const ninetyDaysAgo = new Date(today);
  ninetyDaysAgo.setDate(today.getDate() - 90);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(ninetyDaysAgo), end: fmt(today) };
}

export default function NewBacktestForm({ tickers }: Props) {
  const router = useRouter();
  const defaults = defaultDateRange();

  // Form state
  const [ticker, setTicker] = useState(tickers[0] || "");
  const [strategy, setStrategy] = useState<"buy_and_hold" | "sma_crossover">("buy_and_hold");
  const [startDate, setStartDate] = useState(defaults.start);
  const [endDate, setEndDate] = useState(defaults.end);
  const [initialCapital, setInitialCapital] = useState(10000);

  // Strategy-specific params
  const [fastWindow, setFastWindow] = useState(50);
  const [slowWindow, setSlowWindow] = useState(200);

  // Submission state
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setIsRunning(true);

    const strategy_params: Record<string, unknown> =
      strategy === "sma_crossover"
        ? { fast_window: fastWindow, slow_window: slowWindow }
        : {};

    const result = await runBacktest({
      ticker,
      strategy_name: strategy,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      strategy_params,
    });

    if (!result.ok) {
      setError(result.message);
      setIsRunning(false);
      return;
    }

    // On success: go back to the list. (When detail page exists, redirect there instead.)
    router.push("/backtests");
    router.refresh();
  }

  return (
    <div className="space-y-4">
      {/* Ticker */}
      <div>
        <label className="block text-sm font-medium mb-1">Ticker</label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          disabled={isRunning}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50"
        >
          {tickers.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Strategy */}
      <div>
        <label className="block text-sm font-medium mb-1">Strategy</label>
        <select
          value={strategy}
          onChange={(e) => setStrategy(e.target.value as typeof strategy)}
          disabled={isRunning}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50"
        >
          <option value="buy_and_hold">Buy and Hold</option>
          <option value="sma_crossover">SMA Crossover</option>
        </select>
      </div>

      {/* Date range */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            disabled={isRunning}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={isRunning}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50"
          />
        </div>
      </div>

      {/* Initial capital */}
      <div>
        <label className="block text-sm font-medium mb-1">
          Initial Capital ($)
        </label>
        <input
          type="number"
          min={1}
          step={100}
          value={initialCapital}
          onChange={(e) => setInitialCapital(Number(e.target.value))}
          disabled={isRunning}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50 tabular-nums"
        />
      </div>

      {/* Strategy-specific fields */}
      {strategy === "sma_crossover" && (
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-md">
          <div>
            <label className="block text-sm font-medium mb-1">Fast Window</label>
            <input
              type="number"
              min={2}
              value={fastWindow}
              onChange={(e) => setFastWindow(Number(e.target.value))}
              disabled={isRunning}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50 tabular-nums"
            />
            <p className="text-xs text-gray-500 mt-1">e.g. 20 or 50 days</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Slow Window</label>
            <input
              type="number"
              min={3}
              value={slowWindow}
              onChange={(e) => setSlowWindow(Number(e.target.value))}
              disabled={isRunning}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 disabled:opacity-50 tabular-nums"
            />
            <p className="text-xs text-gray-500 mt-1">e.g. 50 or 200 days</p>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="rounded-md border border-red-300 dark:border-red-700 p-3 bg-red-50 dark:bg-red-950">
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Submit */}
      <div className="pt-2">
        <button
          onClick={handleSubmit}
          disabled={isRunning}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isRunning ? "Running..." : "Run Backtest"}
        </button>
      </div>
    </div>
  );
}