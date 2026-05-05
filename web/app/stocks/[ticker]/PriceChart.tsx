"use client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/** Matches `h-72`; numeric height avoids Recharts width(-1)/height(-1) warnings with %-width. */
const CHART_HEIGHT_PX = 288;

export type ChartPoint = {
  date: string;   // YYYY-MM-DD
  close: number;
};

type Props = {
  data: ChartPoint[];
};

export default function PriceChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-500">
        No price data to chart.
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 h-72">
      <ResponsiveContainer width="100%" height={CHART_HEIGHT_PX}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value: string) => value.slice(5)} // MM-DD
          />
          <YAxis
            tick={{ fontSize: 12 }}
            domain={["auto", "auto"]}
            tickFormatter={(value: number) => `$${value.toFixed(0)}`}
          />
          <Tooltip
            formatter={(value) =>
                typeof value === "number" ? [`$${value.toFixed(2)}`, "Close"] : [String(value), "Close"]
              }           
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}