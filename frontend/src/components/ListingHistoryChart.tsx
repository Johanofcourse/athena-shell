import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ListingEvent } from "../types";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });

interface Props {
  events: ListingEvent[];
}

export function ListingHistoryChart({ events }: Props) {
  const pricePoints = events
    .filter((e) => e.price != null)
    .map((e) => ({
      date: e.event_date,
      label: dateFormatter.format(new Date(e.event_date)),
      price: e.price as number,
      type: e.event_type,
    }));

  if (pricePoints.length === 0) {
    return <p className="empty-state">No price history recorded.</p>;
  }

  return (
    <div className="history-chart">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={pricePoints} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => currency.format(v)}
            tick={{ fontSize: 12, fill: "var(--text-muted)" }}
            axisLine={false}
            tickLine={false}
            width={80}
          />
          <Tooltip
            formatter={(value) => currency.format(Number(value))}
            labelFormatter={(label, payload) =>
              payload?.[0]?.payload ? `${label} · ${payload[0].payload.type}` : label
            }
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
          />
          <Line
            type="stepAfter"
            dataKey="price"
            stroke="var(--accent)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--accent)" }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
