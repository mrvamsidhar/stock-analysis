import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchPrices } from "@/lib/api";

type PageProps = {
  params: Promise<{ ticker: string }>;
};

function dateRange(): { start: string; end: string } {
  const today = new Date();
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(today.getDate() - 7);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(sevenDaysAgo), end: fmt(today) };
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
                {latest.close !== null ? `$${latest.close.toFixed(2)}` : "—"}
              </div>
              <div className="text-sm text-gray-500">
                As of {latest.timestamp.slice(0, 10)}
              </div>
            </>
          ) : (
            <div className="text-gray-500">
              No price data available in the last 7 days.
            </div>
          )}
        </section>

        <p className="text-sm text-gray-400 mt-6">
          Chart and history coming in Phase 4 Checkpoint B.
        </p>
      </div>
    </main>
  );
}