export default function Loading() {
    return (
      <main className="flex min-h-screen flex-col items-center p-8">
        <div className="w-full max-w-2xl">
          {/* Skeleton: matches the structure of the real page */}
          <div className="h-5 w-32 bg-gray-200 dark:bg-gray-800 rounded mb-4 animate-pulse" />
  
          <div className="h-12 w-32 bg-gray-200 dark:bg-gray-800 rounded mb-6 animate-pulse" />
  
          <section className="rounded-lg border border-gray-300 dark:border-gray-700 p-6">
            <div className="h-4 w-24 bg-gray-200 dark:bg-gray-800 rounded mb-2 animate-pulse" />
            <div className="h-8 w-32 bg-gray-200 dark:bg-gray-800 rounded mb-4 animate-pulse" />
            <div className="h-4 w-40 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          </section>
  
          <section className="mt-6">
            <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded mb-3 animate-pulse" />
            <div className="w-full h-72 bg-gray-100 dark:bg-gray-900 rounded animate-pulse" />
          </section>
        </div>
      </main>
    );
  }