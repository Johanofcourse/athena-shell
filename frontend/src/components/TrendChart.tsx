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
import { formatMetricValue } from "../format";
import type { MarketMetricPoint, MetricName } from "../types";

// Leads with the theme tokens (stays in sync if the palette ever changes
// again), then a few extra hues for a 4th+ metro on the same chart - kept
// within the Attic-pottery family (clay, bronze, ochre, slate) rather
// than reaching for a generic chart-library rainbow that would clash
// against a terracotta/cream palette.
const COLORS = ["var(--accent)", "var(--danger)", "var(--success)", "#8a7355", "#c9954f", "#6f7d82"];

const dateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric" });

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
  metric: MetricName;
}

export function TrendChart({ points, metric }: Props) {
  if (points.length === 0) return null;
  const { rows, metros } = pivotByPeriod(points);

  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
            interval={Math.max(0, Math.floor(rows.length / 6) - 1)}
            padding={{ left: 8, right: 8 }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
            width={90}
            tickFormatter={(v: number) => formatMetricValue(metric, v)}
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
          {metros.length > 1 && (
            <Legend wrapperStyle={{ fontSize: 13, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }} />
          )}
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
