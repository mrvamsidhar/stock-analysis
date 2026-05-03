import { fetchPrices, type PricesResult } from "@/lib/api";

const TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"];

function dateRange(): { start: string; end: string } {
  const today = new Date();
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(today.getDate() - 7);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(sevenDaysAgo), end: fmt(today) };
}

type Row = {
  ticker: string;
  result: PricesResult;
};

export default async function WatchlistPage() {
  const { start, end } = dateRange();

  const rows: Row[] = await Promise.all(
    TICKERS.map(async (ticker) => ({
      ticker,
      result: await fetchPrices(ticker, start, end),
    }))
  );

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl font-bold mb-2">Watchlist</h1>
        <p className="text-sm text-gray-500 mb-6">
          Latest close, last 7 days ({start} to {end})
        </p>

        <div className="rounded-lg border border-gray-300 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold">Ticker</th>
                <th className="text-right px-4 py-3 text-sm font-semibold">Latest Close</th>
                <th className="text-right px-4 py-3 text-sm font-semibold">As of</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ ticker, result }) => (
                <WatchlistRow key={ticker} ticker={ticker} result={result} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

function WatchlistRow({
  ticker,
  result,
}: {
  ticker: string;
  result: PricesResult;
}) {
  if (!result.ok) {
    return (
      <tr className="border-t border-gray-200 dark:border-gray-800">
        <td className="px-4 py-3 font-mono font-medium">{ticker}</td>
        <td className="px-4 py-3 text-right text-red-600 dark:text-red-400" colSpan={2}>
          {result.error}
        </td>
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
      <td className="px-4 py-3 text-right text-gray-500 tabular-nums">{dateStr}</td>
    </tr>
  );
}