import Link from "next/link";

export default function StockNotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Ticker not found</h1>
        <p className="text-gray-500 mb-6">
          We don&apos;t have data for that ticker.
        </p>
        <Link
          href="/watchlist"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          &larr; Back to watchlist
        </Link>
      </div>
    </main>
  );
}