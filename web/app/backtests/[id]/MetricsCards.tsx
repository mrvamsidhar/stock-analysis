import type { BacktestResult } from "@/lib/api";

type Props = {
  result: BacktestResult;
};

export default function MetricsCards({ result }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <ReturnCard total_return={result.total_return} />
      <DrawdownCard max_drawdown={result.max_drawdown} />
      <SharpeCard sharpe_ratio={result.sharpe_ratio} />
      <TradesCard num_trades={result.num_trades} />
      <PositionCard is_open_at_end={result.is_open_at_end} />
    </div>
  );
}

function Card({
  label,
  value,
  sublabel,
  valueColor,
}: {
  label: string;
  value: string;
  sublabel?: string;
  valueColor?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-300 dark:border-gray-700 p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-1">
        {label}
      </div>
      <div
        className={`text-2xl font-semibold tabular-nums ${
          valueColor ?? "text-gray-900 dark:text-gray-100"
        }`}
      >
        {value}
      </div>
      {sublabel && (
        <div className="text-xs text-gray-500 mt-1">{sublabel}</div>
      )}
    </div>
  );
}

function ReturnCard({ total_return }: { total_return: number }) {
  const pct = (total_return * 100).toFixed(2);
  const isPositive = total_return >= 0;
  return (
    <Card
      label="Total Return"
      value={`${isPositive ? "+" : ""}${pct}%`}
      valueColor={
        isPositive
          ? "text-green-600 dark:text-green-400"
          : "text-red-600 dark:text-red-400"
      }
    />
  );
}

function DrawdownCard({ max_drawdown }: { max_drawdown: number }) {
  const pct = (max_drawdown * 100).toFixed(2);
  return (
    <Card
      label="Max Drawdown"
      value={`−${pct}%`}
      sublabel="Worst peak-to-trough"
    />
  );
}

function SharpeCard({ sharpe_ratio }: { sharpe_ratio: number }) {
  const formatted = sharpe_ratio.toFixed(2);
  let quality: string;
  if (sharpe_ratio < 0) quality = "Negative";
  else if (sharpe_ratio < 1) quality = "Mediocre";
  else if (sharpe_ratio < 2) quality = "Good";
  else quality = "Excellent";

  return (
    <Card
      label="Sharpe Ratio"
      value={formatted}
      sublabel={quality}
    />
  );
}

function TradesCard({ num_trades }: { num_trades: number }) {
  return (
    <Card
      label="Trades"
      value={num_trades.toString()}
      sublabel="Round-trips completed"
    />
  );
}

function PositionCard({ is_open_at_end }: { is_open_at_end: boolean }) {
  return (
    <Card
      label="Position"
      value={is_open_at_end ? "Open" : "Closed"}
      sublabel={is_open_at_end ? "Mark-to-market" : "Realized"}
    />
  );
}