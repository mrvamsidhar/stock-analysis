import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchBacktest, fetchPrices } from "@/lib/api";
import MetricsCards from "./MetricsCards";
import EquityChart from "./EquityChart";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function BacktestDetailPage({ params }: PageProps) {
  const { id } = await params;

  const result = await fetchBacktest(id);

  if (!result.ok) {
    if (result.status === 404) {
      notFound();
    }
    // Other errors (500, network down) — show inline error
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-4xl">
          <Link
            href="/backtests"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
          >
            ← Back to backtests
          </Link>
          <div className="rounded-lg border border-red-300 dark:border-red-700 p-6 bg-red-50 dark:bg-red-950">
            <p className="text-red-700 dark:text-red-300">
              Could not load backtest: {result.message}
            </p>
          </div>
        </div>
      </main>
    );
  }

  const run = result.data;
  const r = run.result;
  const pricesResult = await fetchPrices(r.ticker, r.start_date, r.end_date);
  const pricesForComparison =
    pricesResult.ok ? pricesResult.data.prices : [];
  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-4xl">
        <Link
          href="/backtests"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
        >
          ← Back to backtests
        </Link>

        <div className="mb-6">
          <h1 className="text-3xl font-bold font-mono mb-2">{r.ticker}</h1>
          <p className="text-gray-600 dark:text-gray-400">
            <span className="font-medium">{r.strategy_name}</span>
            {" · "}
            <span className="tabular-nums">
              {r.start_date} → {r.end_date}
            </span>
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Run at {new Date(run.created_at).toLocaleString()}
          </p>
        </div>

        <div className="mb-6">
            <MetricsCards result={r} />
        </div>

        <section className="rounded-lg border border-gray-300 dark:border-gray-700 p-6 mb-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Equity Curve
          </h2>
          <EquityChart equityCurve={r.equity_curve} initialCapital={r.initial_capital} pricesForComparison={pricesForComparison}/>
        </section>

        {/* Strategy params — small but useful */}
        {Object.keys(run.strategy_params).length > 0 && (
          <section className="text-sm text-gray-600 dark:text-gray-400">
            <h3 className="font-semibold mb-1">Strategy parameters</h3>
            <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto">
              {JSON.stringify(run.strategy_params, null, 2)}
            </pre>
          </section>
        )}
      </div>
    </main>
  );
}