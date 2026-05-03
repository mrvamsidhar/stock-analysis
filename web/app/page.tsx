import { fetchHealth, type HealthResponse } from "@/lib/api";

export default async function HomePage() {
  let health: HealthResponse | null = null;
  let fetchError: string | null = null;

  try {
    health = await fetchHealth();
  } catch (err) {
    fetchError = err instanceof Error ? err.message : "Unknown error";
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold mb-6">Stock Analysis</h1>

      <section className="w-full max-w-md rounded-lg border border-gray-300 dark:border-gray-700 p-6">
        <h2 className="text-xl font-semibold mb-4">API Status</h2>

        {fetchError && (
          <div className="text-red-600 dark:text-red-400">
            <p className="font-medium">Could not reach the API</p>
            <p className="text-sm mt-2">{fetchError}</p>
            <p className="text-sm mt-2 text-gray-500">
              Make sure the FastAPI server is running on{" "}
              <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
                localhost:8000
              </code>
              .
            </p>
          </div>
        )}

        {health && (
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">Service:</dt>
              <dd
                className={
                  health.status === "ok"
                    ? "text-green-600 dark:text-green-400 font-medium"
                    : "text-yellow-600 dark:text-yellow-400 font-medium"
                }
              >
                {health.status}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">Database:</dt>
              <dd
                className={
                  health.database === "reachable"
                    ? "text-green-600 dark:text-green-400 font-medium"
                    : "text-red-600 dark:text-red-400 font-medium"
                }
              >
                {health.database}
              </dd>
            </div>
          </dl>
        )}
      </section>
    </main>
  );
}