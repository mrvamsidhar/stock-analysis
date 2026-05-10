import Link from "next/link";

export default function BacktestNotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center max-w-md">
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <p className="text-xl mb-2">Backtest not found</p>
        <p className="text-gray-500 mb-6">
          That backtest id doesn&apos;t exist or has been deleted.
        </p>
        <Link
          href="/backtests"
          className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
        >
          ← Back to backtests
        </Link>
      </div>
    </main>
  );
}