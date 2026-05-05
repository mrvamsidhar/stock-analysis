import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchPrices } from "@/lib/api";
import PriceChart, { type ChartPoint } from "./PriceChart";

const HISTORY_DAYS = 90;

type PageProps = {
  params: Promise<{ ticker: string }>;
};

function dateRange(): { start: string; end: string } {
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(today.getDate() - HISTORY_DAYS);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(startDate), end: fmt(today) };
}

export default async function StockDetailPage({ params }: PageProps) {
  const { ticker: rawTicker } = await params;
  const ticker = rawTicker.toUpperCase();

  const { start, end } = dateRange();
  const result = await fetchPrices(ticker, start, end);

  // Unknown ticker -> Next.js renders the closest not-found.tsx (or a default 404).
  if (!result.ok) {
    notFound();
  }

  const bars = result.data.prices;
  const latest = bars.length > 0 ? bars[bars.length - 1] : null;

  // Filter out rows with no close price (rare but possible -- DB allows nulls).
  // Recharts can't plot nulls; dropping them avoids gaps in the line.
  const chartData: ChartPoint[] = bars
    .filter((bar) => bar.close !== null)
    .map((bar) => ({
      date: bar.timestamp.slice(0, 10),
      close: bar.close as number,
    }));

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-2xl">
        <Link
          href="/watchlist"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
        >
          &larr; Back to watchlist
        </Link>

        <h1 className="text-4xl font-bold font-mono mb-6">{ticker}</h1>

        <section className="rounded-lg border border-gray-300 dark:border-gray-700 p-6">
          {latest ? (
            <>
              <div className="text-sm text-gray-500 mb-1">Latest close</div>
              <div className="text-3xl font-semibold tabular-nums mb-4">
                {latest.close !== null ? `$${latest.close.toFixed(2)}` : "-"}
              </div>
              <div className="text-sm text-gray-500">
                As of {latest.timestamp.slice(0, 10)}
              </div>
            </>
          ) : (
            <div className="text-gray-500">
              No price data available in the last {HISTORY_DAYS} days.
            </div>
          )}
        </section>

        <section className="mt-6">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-semibold">
              Price (last {HISTORY_DAYS} days)
            </h2>
            {latest && (
              <span className="text-xs text-gray-500">
                Last updated {latest.timestamp.slice(0, 10)}
              </span>
            )}
          </div>
          <PriceChart data={chartData} />
        </section>
      </div>
    </main>
  );
}