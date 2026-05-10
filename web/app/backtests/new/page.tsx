import Link from "next/link";
import { fetchBacktests } from "@/lib/api";
import NewBacktestForm from "./NewBacktestForm";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function fetchTickers(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/tickers`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch tickers: ${response.statusText}`);
  }
  return response.json();
}

export default async function NewBacktestPage() {
  let tickers: string[] = [];
  let fetchError: string | null = null;

  try {
    tickers = await fetchTickers();
  } catch (err) {
    fetchError = err instanceof Error ? err.message : "Unknown error";
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-2xl">
        <Link
          href="/backtests"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
        >
          ← Back to backtests
        </Link>

        <h1 className="text-3xl font-bold mb-6">New Backtest</h1>

        {fetchError ? (
          <div className="rounded-lg border border-red-300 dark:border-red-700 p-6 bg-red-50 dark:bg-red-950">
            <p className="text-red-700 dark:text-red-300">
              Could not load tickers: {fetchError}
            </p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-2">
              Make sure the API is running.
            </p>
          </div>
        ) : (
          <NewBacktestForm tickers={tickers} />
        )}
      </div>
    </main>
  );
}