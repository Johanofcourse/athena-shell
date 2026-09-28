import { formatMetricValue } from "./format";
import type { MarketMetricPoint, MetricName } from "./types";

// timeZone: "UTC" is load-bearing, not decorative: period strings are
// date-only ("2024-02-01"), which `new Date()` parses as UTC midnight.
// Without pinning the formatter to UTC too, anyone west of UTC (all of
// the US) sees that rendered in their local timezone - which pushes the
// 1st of the month back into the previous day, so every peak/trough
// callout silently named the wrong month. Caught by a test, not by eye.
const monthYearFormatter = new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric", timeZone: "UTC" });

/** Deterministic, computed straight from the returned data - not a second
 * LLM call, so it can never claim something the numbers don't back up. */
export function summarizeResults(
  points: MarketMetricPoint[],
  metric: MetricName,
  mode: "period" | "value",
): string {
  if (points.length === 0) return "";

  if (mode === "value") {
    if (points.length === 1) {
      return `${points[0].metro}: ${formatMetricValue(metric, points[0].value)}.`;
    }
    const top = points[0];
    const bottom = points[points.length - 1];
    return `${top.metro} leads at ${formatMetricValue(metric, top.value)}; ${bottom.metro} is lowest at ${formatMetricValue(metric, bottom.value)}.`;
  }

  const byMetro = new Map<string, MarketMetricPoint[]>();
  for (const p of points) {
    if (!byMetro.has(p.metro)) byMetro.set(p.metro, []);
    byMetro.get(p.metro)!.push(p);
  }

  const sentences: string[] = [];
  for (const [metro, series] of byMetro) {
    const sorted = [...series].sort((a, b) => a.period.localeCompare(b.period));
    if (sorted.length < 2) {
      sentences.push(`${metro}: ${formatMetricValue(metric, sorted[0].value)}.`);
      continue;
    }

    const first = sorted[0];
    const last = sorted[sorted.length - 1];
    const peak = sorted.reduce((a, b) => (b.value > a.value ? b : a));
    const trough = sorted.reduce((a, b) => (b.value < a.value ? b : a));
    const pctChange = first.value !== 0 ? ((last.value - first.value) / first.value) * 100 : 0;
    const direction = pctChange > 0.05 ? "up" : pctChange < -0.05 ? "down" : "flat";

    let sentence = `${metro}: ${formatMetricValue(metric, first.value)} → ${formatMetricValue(metric, last.value)} (${direction} ${Math.abs(pctChange).toFixed(1)}%)`;

    const extremum = peak.value !== first.value && peak.value !== last.value ? peak : trough.value !== first.value && trough.value !== last.value ? trough : null;
    if (extremum) {
      const label = extremum === peak ? "peaked" : "bottomed out";
      sentence += `, ${label} at ${formatMetricValue(metric, extremum.value)} in ${monthYearFormatter.format(new Date(extremum.period))}`;
    }

    sentences.push(sentence + ".");
  }
  return sentences.join(" ");
}
