import { useMemo, useState } from "react";
import { getMetricValue } from "../analytics";
import { formatMetricValue } from "../format";
import { DASHBOARD_METRICS, METRIC_LABELS } from "../metricLabels";
import type { MetricName, MetroSnapshot } from "../types";

interface Props {
  snapshots: MetroSnapshot[];
}

export function MetroCompareTable({ snapshots }: Props) {
  const [sortMetric, setSortMetric] = useState<MetricName>("median_sale_price");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const rows = useMemo(() => {
    // Metros missing the sort column always sink to the bottom regardless
    // of direction - an undefined value isn't "smallest" or "largest",
    // and flipping it to the top on ascending sort would read as the
    // metro leading the ranking rather than lacking data for it.
    const withValue: { snapshot: MetroSnapshot; value: number }[] = [];
    const withoutValue: MetroSnapshot[] = [];
    for (const s of snapshots) {
      const value = getMetricValue(s, sortMetric);
      if (value === undefined) withoutValue.push(s);
      else withValue.push({ snapshot: s, value });
    }
    withValue.sort((a, b) => (sortDir === "asc" ? a.value - b.value : b.value - a.value));
    return [...withValue.map((r) => r.snapshot), ...withoutValue];
  }, [snapshots, sortMetric, sortDir]);

  function handleSort(metric: MetricName) {
    if (metric === sortMetric) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortMetric(metric);
      setSortDir("desc");
    }
  }

  return (
    <div className="compare-table-wrap">
      <table className="compare-table">
        <thead>
          <tr>
            <th scope="col">Metro</th>
            {DASHBOARD_METRICS.map((metric) => (
              <th key={metric} scope="col" aria-sort={sortMetric === metric ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                <button type="button" onClick={() => handleSort(metric)}>
                  {METRIC_LABELS[metric]}
                  {sortMetric === metric && <span className="sort-arrow">{sortDir === "asc" ? " ▲" : " ▼"}</span>}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.metro}>
              <th scope="row">{s.metro}</th>
              {DASHBOARD_METRICS.map((metric) => {
                const value = getMetricValue(s, metric);
                return (
                  <td key={metric}>{value === undefined ? "—" : formatMetricValue(metric, value)}</td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
