import Link from "next/link";
import { fetchBacktests, type BacktestRunSummary } from "@/lib/api";

export default async function BacktestsListPage() {
  const result = await fetchBacktests();

  if (!result.ok) {
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-4xl">
          <h1 className="text-3xl font-bold mb-6">Backtests</h1>
          <div className="rounded-lg border border-red-300 dark:border-red-700 p-6 bg-red-50 dark:bg-red-950">
            <p className="text-red-700 dark:text-red-300">
              Could not load backtests: {result.message}
            </p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-2">
              Is the API running? Try{" "}
              <code className="px-1 py-0.5 bg-red-100 dark:bg-red-900 rounded">
                docker start trading_db
              </code>{" "}
              and{" "}
              <code className="px-1 py-0.5 bg-red-100 dark:bg-red-900 rounded">
                uvicorn app.main:app --reload --port 8000
              </code>
            </p>
          </div>
        </div>
      </main>
    );
  }

  const runs = result.data;

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Backtests</h1>
          <Link
            href="/backtests/new"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
          >
            + New backtest
          </Link>
        </div>

        {runs.length === 0 ? (
          <div className="rounded-lg border border-gray-300 dark:border-gray-700 p-8 text-center">
            <p className="text-gray-500 mb-3">No backtests yet.</p>
            <Link
              href="/backtests/new"
              className="text-blue-600 hover:underline"
            >
              Run your first one →
            </Link>
          </div>
        ) : (
          <BacktestsTable runs={runs} />
        )}
      </div>
    </main>
  );
}

export function BacktestsTable({ runs }: { runs: BacktestRunSummary[] }) {
  return (
    <div className="rounded-lg border border-gray-300 dark:border-gray-700 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr className="text-left">
            <th className="px-4 py-3 font-semibold">Ticker</th>
            <th className="px-4 py-3 font-semibold">Strategy</th>
            <th className="px-4 py-3 font-semibold">Range</th>
            <th className="px-4 py-3 font-semibold text-right">Return</th>
            <th className="px-4 py-3 font-semibold text-right">Drawdown</th>
            <th className="px-4 py-3 font-semibold text-right">Sharpe</th>
            <th className="px-4 py-3 font-semibold text-right">Trades</th>
            <th className="px-4 py-3 font-semibold text-right">Run at</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <BacktestRow key={run.id} run={run} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BacktestRow({ run }: { run: BacktestRunSummary }) {
  const returnPct = (run.total_return * 100).toFixed(2);
  const drawdownPct = (run.max_drawdown * 100).toFixed(2);
  const sharpe = run.sharpe_ratio.toFixed(2);
  const isPositive = run.total_return >= 0;
  const createdAt = new Date(run.created_at).toLocaleString();

  return (
    <tr className="border-t border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900">
      <td className="px-4 py-3 font-mono font-medium">
        <Link
          href={`/backtests/${run.id}`}
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          {run.ticker}
        </Link>
      </td>
      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
        {run.strategy_name}
      </td>
      <td className="px-4 py-3 text-gray-600 dark:text-gray-400 tabular-nums">
        {run.start_date} → {run.end_date}
      </td>
      <td
        className={`px-4 py-3 text-right tabular-nums font-medium ${
          isPositive
            ? "text-green-600 dark:text-green-400"
            : "text-red-600 dark:text-red-400"
        }`}
      >
        {isPositive ? "+" : ""}
        {returnPct}%
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
        −{drawdownPct}%
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
        {sharpe}
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
        {run.num_trades}
      </td>
      <td className="px-4 py-3 text-right text-gray-500 text-xs">
        {createdAt}
      </td>
    </tr>
  );
}