"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { EquityPoint, PriceBar } from "@/lib/api";

const CHART_HEIGHT_PX = 320;

type ChartRow = {
  date: string;
  strategy?: number;
  buyhold?: number;
};

type Props = {
  equityCurve: EquityPoint[];
  initialCapital: number;
  pricesForComparison: PriceBar[];
};

/**
 * Compute the buy-and-hold equity curve from raw prices.
 * shares = initialCapital / firstClose
 * for each bar: equity = shares * close
 */
function computeBuyHoldCurve(
  prices: PriceBar[],
  initialCapital: number
): { date: string; value: number }[] {
  const validPrices = prices.filter(
    (p): p is PriceBar & { close: number } => p.close !== null
  );
  if (validPrices.length === 0) return [];

  const firstClose = validPrices[0].close;
  if (firstClose <= 0) return [];

  const shares = initialCapital / firstClose;
  return validPrices.map((p) => ({
    date: p.timestamp.slice(0, 10),
    value: shares * p.close,
  }));
}

/**
 * Merge strategy curve and buy-hold curve into a single array indexed by date.
 */
function mergeChartData(
  strategy: EquityPoint[],
  buyhold: { date: string; value: number }[]
): ChartRow[] {
  const byDate = new Map<string, ChartRow>();

  for (const point of strategy) {
    byDate.set(point.date, { date: point.date, strategy: point.value });
  }
  for (const point of buyhold) {
    const existing = byDate.get(point.date);
    if (existing) {
      existing.buyhold = point.value;
    } else {
      byDate.set(point.date, { date: point.date, buyhold: point.value });
    }
  }

  return Array.from(byDate.values()).sort((a, b) =>
    a.date.localeCompare(b.date)
  );
}

export default function EquityChart({
  equityCurve,
  initialCapital,
  pricesForComparison,
}: Props) {
  if (equityCurve.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-500">
        No equity data to chart.
      </div>
    );
  }

  const buyHoldCurve = computeBuyHoldCurve(pricesForComparison, initialCapital);
  const chartData = mergeChartData(equityCurve, buyHoldCurve);
  const hasComparison = buyHoldCurve.length > 0;

  return (
    <div className="w-full min-w-0">
      {!hasComparison && pricesForComparison.length === 0 && (
        <p className="text-xs text-gray-500 mb-2">
          Buy-and-hold comparison unavailable (no price data for this range).
        </p>
      )}
      <ResponsiveContainer width="100%" height={CHART_HEIGHT_PX}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(value: string) => value.slice(5)}
            minTickGap={30}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            domain={["auto", "auto"]}
            tickFormatter={(value: number) =>
              `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
            }
            width={70}
          />
          <Tooltip
            formatter={(value, name) => {
              const label = name === "strategy" ? "Strategy" : "Buy & Hold";
              if (typeof value !== "number") return [String(value), label];
              return [
                `$${value.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`,
                label,
              ];
            }}
          />
          <Legend
            verticalAlign="top"
            height={28}
            formatter={(value) => (value === "strategy" ? "Strategy" : "Buy & Hold")}
          />
          <Line
            type="monotone"
            dataKey="strategy"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
          {hasComparison && (
            <Line
              type="monotone"
              dataKey="buyhold"
              stroke="#9ca3af"
              strokeWidth={2}
              strokeDasharray="4 3"
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}