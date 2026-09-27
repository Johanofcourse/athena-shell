import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MarketMetricPoint } from "../types";

interface Props {
  points: MarketMetricPoint[];
}

export function RankingChart({ points }: Props) {
  if (points.length === 0) return null;

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={Math.max(220, points.length * 34)}>
        <BarChart data={points} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 12, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
          <YAxis
            dataKey="metro"
            type="category"
            width={150}
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
