import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMetricValue } from "../format";
import type { MarketMetricPoint, MetricName } from "../types";

interface Props {
  points: MarketMetricPoint[];
  metric: MetricName;
}

export function RankingChart({ points, metric }: Props) {
  if (points.length === 0) return null;

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
            tickFormatter={(v: number) => formatMetricValue(metric, v)}
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
            formatter={(value) => formatMetricValue(metric, Number(value))}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[0, 0, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
