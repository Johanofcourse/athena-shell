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
import type { MarketMetricPoint } from "../types";

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"];

const dateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", year: "2-digit" });

function pivotByPeriod(points: MarketMetricPoint[]): { rows: Record<string, string | number>[]; metros: string[] } {
  const metros = Array.from(new Set(points.map((p) => p.metro)));
  const byPeriod = new Map<string, Record<string, string | number>>();
  for (const p of points) {
    if (!byPeriod.has(p.period)) {
      byPeriod.set(p.period, { period: p.period, label: dateFormatter.format(new Date(p.period)) });
    }
    byPeriod.get(p.period)![p.metro] = p.value;
  }
  const rows = Array.from(byPeriod.values()).sort((a, b) =>
    String(a.period).localeCompare(String(b.period)),
  );
  return { rows, metros };
}

interface Props {
  points: MarketMetricPoint[];
}

export function TrendChart({ points }: Props) {
  if (points.length === 0) return null;
  const { rows, metros } = pivotByPeriod(points);

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            axisLine={false}
            tickLine={false}
            width={70}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          {metros.length > 1 && <Legend wrapperStyle={{ fontSize: 13 }} />}
          {metros.map((metro, i) => (
            <Line
              key={metro}
              type="monotone"
              dataKey={metro}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
