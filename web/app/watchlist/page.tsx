import WatchlistClient from "./WatchlistClient";

export default function WatchlistPage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl font-bold mb-2">Watchlist</h1>
        <p className="text-sm text-gray-500 mb-6">Latest close, last 7 days</p>
        <WatchlistClient />
      </div>
    </main>
  );
}