export default function Loading() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="w-full max-w-4xl">
        {/* Back link skeleton */}
        <div className="h-5 w-32 bg-gray-200 dark:bg-gray-800 rounded mb-4 animate-pulse" />

        {/* Header skeletons */}
        <div className="mb-6 space-y-2">
          <div className="h-10 w-32 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-5 w-72 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-4 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        </div>

        {/* Metrics card skeleton */}
        <div className="rounded-lg border border-gray-300 dark:border-gray-700 p-6 mb-6 h-32 bg-gray-100 dark:bg-gray-900 animate-pulse" />

        {/* Chart skeleton */}
        <div className="rounded-lg border border-gray-300 dark:border-gray-700 p-6 mb-6 h-80 bg-gray-100 dark:bg-gray-900 animate-pulse" />
      </div>
    </main>
  );
}