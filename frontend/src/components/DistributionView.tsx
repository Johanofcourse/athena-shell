import { useMemo, useState } from "react";
import { summaryStats, valuesForMetric } from "../analytics";
import { formatMetricValue } from "../format";
import { DASHBOARD_METRICS, METRIC_LABELS } from "../metricLabels";
import type { MarketMetricPoint, MetricName, MetroSnapshot } from "../types";
import { RankingChart } from "./RankingChart";

interface Props {
  snapshots: MetroSnapshot[];
}

export function DistributionView({ snapshots }: Props) {
  const [metric, setMetric] = useState<MetricName>("natural_hazard_risk_score");

  const values = useMemo(() => valuesForMetric(snapshots, metric), [snapshots, metric]);
  const stats = useMemo(() => summaryStats(values.map((v) => v.value)), [values]);

  // RankingChart only reads `metro`/`value` off each point (see its own
  // render) - `period` is part of MarketMetricPoint's shape but never
  // displayed, so a placeholder here lets this view reuse that component
  // exactly rather than forking a near-duplicate bar chart.
  const points: MarketMetricPoint[] = useMemo(
    () => [...values].sort((a, b) => b.value - a.value).map((v) => ({ metro: v.metro, period: "", value: v.value })),
    [values],
  );

  return (
    <div>
      <div className="metric-pickers">
        <label>
          Metric
          <select value={metric} onChange={(e) => setMetric(e.target.value as MetricName)}>
            {DASHBOARD_METRICS.map((m) => (
              <option key={m} value={m}>{METRIC_LABELS[m]}</option>
            ))}
          </select>
        </label>
      </div>

      {stats === null ? (
        <p className="empty-state">No metros have data for this metric.</p>
      ) : (
        <>
          <dl className="stats-strip">
            <div>
              <dt>Metros</dt>
              <dd>{stats.count}</dd>
            </div>
            <div>
              <dt>Mean</dt>
              <dd>{formatMetricValue(metric, stats.mean)}</dd>
            </div>
            <div>
              <dt>Median</dt>
              <dd>{formatMetricValue(metric, stats.median)}</dd>
            </div>
            <div>
              <dt>Std. dev</dt>
              <dd>{formatMetricValue(metric, stats.stdev)}</dd>
            </div>
            <div>
              <dt>Range</dt>
              <dd>{formatMetricValue(metric, stats.min)} – {formatMetricValue(metric, stats.max)}</dd>
            </div>
          </dl>
          <RankingChart points={points} metric={metric} />
        </>
      )}
    </div>
  );
}
