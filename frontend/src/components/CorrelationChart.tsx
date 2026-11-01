import { useMemo, useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { linearRegression, pairSnapshotValues, pearsonCorrelation, type XYPoint } from "../analytics";
import { formatMetricValue } from "../format";
import { DASHBOARD_METRICS, METRIC_LABELS } from "../metricLabels";
import type { MetricName, MetroSnapshot } from "../types";

interface Props {
  snapshots: MetroSnapshot[];
}

interface CorrelationTooltipProps {
  active?: boolean;
  payload?: { payload: XYPoint }[];
  metricX: MetricName;
  metricY: MetricName;
}

function CorrelationTooltip({ active, payload, metricX, metricY }: CorrelationTooltipProps) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        padding: "8px 12px",
        fontSize: 13,
        fontFamily: "var(--font-mono)",
        color: "var(--text)",
      }}
    >
      <strong>{point.metro}</strong>
      <div>{METRIC_LABELS[metricX]}: {formatMetricValue(metricX, point.x)}</div>
      <div>{METRIC_LABELS[metricY]}: {formatMetricValue(metricY, point.y)}</div>
    </div>
  );
}

function strengthLabel(r: number): string {
  const abs = Math.abs(r);
  if (abs >= 0.7) return "strong";
  if (abs >= 0.4) return "moderate";
  if (abs >= 0.2) return "weak";
  return "negligible";
}

export function CorrelationChart({ snapshots }: Props) {
  const [metricX, setMetricX] = useState<MetricName>("median_household_income");
  const [metricY, setMetricY] = useState<MetricName>("median_sale_price");

  const points = useMemo(() => pairSnapshotValues(snapshots, metricX, metricY), [snapshots, metricX, metricY]);
  const r = useMemo(() => pearsonCorrelation(points), [points]);
  const fit = useMemo(() => linearRegression(points), [points]);

  const trendLine = useMemo(() => {
    if (points.length < 2 || Number.isNaN(fit.slope)) return [];
    const xs = points.map((p) => p.x);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    return [
      { x: minX, y: fit.slope * minX + fit.intercept },
      { x: maxX, y: fit.slope * maxX + fit.intercept },
    ];
  }, [points, fit]);

  return (
    <div className="chart-card">
      <div className="metric-pickers">
        <label>
          X axis
          <select value={metricX} onChange={(e) => setMetricX(e.target.value as MetricName)}>
            {DASHBOARD_METRICS.map((m) => (
              <option key={m} value={m}>{METRIC_LABELS[m]}</option>
            ))}
          </select>
        </label>
        <label>
          Y axis
          <select value={metricY} onChange={(e) => setMetricY(e.target.value as MetricName)}>
            {DASHBOARD_METRICS.map((m) => (
              <option key={m} value={m}>{METRIC_LABELS[m]}</option>
            ))}
          </select>
        </label>
      </div>

      {points.length < 2 ? (
        <p className="empty-state">Not enough metros have both metrics to plot a relationship.</p>
      ) : (
        <>
          <p className="correlation-stat">
            Pearson <em>r</em> = {Number.isNaN(r) ? "n/a" : r.toFixed(2)}
            {!Number.isNaN(r) && ` (${strengthLabel(r)} ${r >= 0 ? "positive" : "negative"})`} across {points.length} metros
          </p>
          <ResponsiveContainer width="100%" height={360}>
            <ComposedChart margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                type="number"
                name={METRIC_LABELS[metricX]}
                tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                tickFormatter={(v: number) => formatMetricValue(metricX, v)}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
              />
              <YAxis
                dataKey="y"
                type="number"
                name={METRIC_LABELS[metricY]}
                tick={{ fontSize: 12, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                tickFormatter={(v: number) => formatMetricValue(metricY, v)}
                axisLine={false}
                tickLine={false}
                width={90}
              />
              <Tooltip
                content={(props: unknown) => (
                  <CorrelationTooltip {...(props as CorrelationTooltipProps)} metricX={metricX} metricY={metricY} />
                )}
              />
              <Scatter data={points} dataKey="y" fill="var(--accent)" />
              {trendLine.length === 2 && (
                <Line data={trendLine} dataKey="y" stroke="var(--danger)" strokeWidth={2} dot={false} legendType="none" />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
