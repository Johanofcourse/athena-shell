import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMetricValue } from "../format";
import type { MarketMetricPoint, MetricName } from "../types";

interface Props {
  points: MarketMetricPoint[];
  metric: MetricName;
  // True for a "change" ranking (sort_by "change") - each point's value
  // is already a computed percent change, not a raw metric value, so it
  // needs its own formatting (e.g. "+27.3%") rather than
  // formatMetricValue, which would render it in the metric's own unit
  // (population's percent change shown as a population count, a dollar
  // sign on a percentage, etc.) - the same distinction
  // summarize_metric_facts/analysis.ts's summarizeResults already make
  // for the narrative text, just applied to the chart's own axis and
  // tooltip here.
  isChangeRanking?: boolean;
}

function formatChangeValue(v: number): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

export function RankingChart({ points, metric, isChangeRanking }: Props) {
  if (points.length === 0) return null;
  const formatValue = (v: number) => (isChangeRanking ? formatChangeValue(v) : formatMetricValue(metric, v));

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={Math.max(220, points.length * 34)}>
        <BarChart data={points} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => formatValue(v)}
          />
          <YAxis
            dataKey="metro"
            type="category"
            width={150}
            tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 0,
              fontSize: 13,
              fontFamily: "var(--font-mono)",
              color: "var(--text)",
            }}
            labelStyle={{ color: "var(--text)" }}
            formatter={(value) => formatValue(Number(value))}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[0, 0, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
