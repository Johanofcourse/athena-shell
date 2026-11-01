import type { MetricName, MetroSnapshot } from "./types";

export interface XYPoint {
  metro: string;
  x: number;
  y: number;
}

/** snapshot.values never has a "rent_to_income_pct" key - the backend's
 * curated snapshot metric list (routers/analytics.py) ships the two raw
 * legs instead, so this is the one metric name that always resolves to
 * the derived ratio rather than a direct lookup. See rentToIncomePct. */
export function getMetricValue(snapshot: MetroSnapshot, metric: MetricName): number | undefined {
  if (metric === "rent_to_income_pct") return rentToIncomePct(snapshot);
  return snapshot.values[metric];
}

/** Every metro with a real value for both metrics - metros missing either
 * leg are left out entirely (same honesty rule as the backend's
 * no_data_metros), never coerced to 0. */
export function pairSnapshotValues(
  snapshots: MetroSnapshot[],
  metricX: MetricName,
  metricY: MetricName,
): XYPoint[] {
  const points: XYPoint[] = [];
  for (const s of snapshots) {
    const x = getMetricValue(s, metricX);
    const y = getMetricValue(s, metricY);
    if (x !== undefined && y !== undefined) points.push({ metro: s.metro, x, y });
  }
  return points;
}

/** Pearson correlation coefficient, -1..1. NaN for fewer than 2 points or
 * when either series has zero variance (undefined, not a misleading 0). */
export function pearsonCorrelation(points: XYPoint[]): number {
  const n = points.length;
  if (n < 2) return NaN;

  const meanX = points.reduce((sum, p) => sum + p.x, 0) / n;
  const meanY = points.reduce((sum, p) => sum + p.y, 0) / n;

  let covariance = 0;
  let varianceX = 0;
  let varianceY = 0;
  for (const p of points) {
    const dx = p.x - meanX;
    const dy = p.y - meanY;
    covariance += dx * dy;
    varianceX += dx * dx;
    varianceY += dy * dy;
  }

  if (varianceX === 0 || varianceY === 0) return NaN;
  return covariance / Math.sqrt(varianceX * varianceY);
}

export interface LinearFit {
  slope: number;
  intercept: number;
}

/** Ordinary least-squares fit (y = slope*x + intercept) for the scatter's
 * trend line. NaN slope/intercept when there's nothing to fit (fewer than
 * 2 points, or every point shares the same x). */
export function linearRegression(points: XYPoint[]): LinearFit {
  const n = points.length;
  if (n < 2) return { slope: NaN, intercept: NaN };

  const meanX = points.reduce((sum, p) => sum + p.x, 0) / n;
  const meanY = points.reduce((sum, p) => sum + p.y, 0) / n;

  let numerator = 0;
  let denominator = 0;
  for (const p of points) {
    numerator += (p.x - meanX) * (p.y - meanY);
    denominator += (p.x - meanX) ** 2;
  }

  if (denominator === 0) return { slope: NaN, intercept: NaN };
  const slope = numerator / denominator;
  return { slope, intercept: meanY - slope * meanX };
}

export interface SummaryStats {
  count: number;
  mean: number;
  median: number;
  min: number;
  max: number;
  stdev: number;
}

/** Population standard deviation (dividing by n, not n-1) - this is the
 * full set of the 50 metros, not a sample drawn from a larger population,
 * so there's no Bessel's-correction case to make here. */
export function summaryStats(values: number[]): SummaryStats | null {
  const n = values.length;
  if (n === 0) return null;

  const sorted = [...values].sort((a, b) => a - b);
  const mean = sorted.reduce((sum, v) => sum + v, 0) / n;
  const mid = Math.floor(n / 2);
  const median = n % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
  const variance = sorted.reduce((sum, v) => sum + (v - mean) ** 2, 0) / n;

  return {
    count: n,
    mean,
    median,
    min: sorted[0],
    max: sorted[n - 1],
    stdev: Math.sqrt(variance),
  };
}

export interface MetroMetricValue {
  metro: string;
  value: number;
}

export function valuesForMetric(snapshots: MetroSnapshot[], metric: MetricName): MetroMetricValue[] {
  const out: MetroMetricValue[] = [];
  for (const s of snapshots) {
    const value = getMetricValue(s, metric);
    if (value !== undefined) out.push({ metro: s.metro, value });
  }
  return out;
}

/** rent_to_income_pct isn't in the snapshot's curated metric set (the
 * backend only ships the two raw legs - see
 * backend/app/routers/analytics.py) - this derives the same ratio the
 * backend's own _run_rent_to_income_query computes server-side for the NL
 * query path, so a metro shown here and asked about in plain English never
 * disagree. Undefined when either leg is missing, never a fabricated 0. */
export function rentToIncomePct(snapshot: MetroSnapshot): number | undefined {
  const rent = snapshot.values.median_rent;
  const income = snapshot.values.median_household_income;
  if (rent === undefined || income === undefined || income === 0) return undefined;
  return ((rent * 12) / income) * 100;
}
