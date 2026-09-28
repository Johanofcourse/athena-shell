import { describe, expect, it } from "vitest";
import { summarizeResults } from "./analysis";
import type { MarketMetricPoint } from "./types";

function point(metro: string, period: string, value: number): MarketMetricPoint {
  return { metro, period, value };
}

describe("summarizeResults", () => {
  it("returns an empty string for no results", () => {
    expect(summarizeResults([], "median_sale_price", "period")).toBe("");
  });

  it("ranking mode with a single point names just that metro", () => {
    const text = summarizeResults([point("Austin, TX", "2026-08-01", 450000)], "median_sale_price", "value");
    expect(text).toBe("Austin, TX: $450,000.");
  });

  it("ranking mode with multiple points names the leader and the lowest (assumes caller pre-sorted)", () => {
    // summarizeResults trusts points[0]/points[last] as leader/lowest -
    // run_market_query's ranking mode always returns pre-sorted results,
    // so this input mirrors that (descending).
    const points = [
      point("Miami, FL", "2026-08-01", 28.4),
      point("Boston, MA", "2026-08-01", 23.5),
      point("Austin, TX", "2026-08-01", 20.1),
    ];
    const text = summarizeResults(points, "rent_to_income_pct", "value");
    expect(text).toBe("Miami, FL leads at 28.4%; Austin, TX is lowest at 20.1%.");
  });

  it("trend mode with a single period just states the value", () => {
    const text = summarizeResults([point("Denver, CO", "2026-08-01", 2000)], "median_rent", "period");
    expect(text).toBe("Denver, CO: $2,000.");
  });

  it("trend mode reports direction and percent change between first and last", () => {
    const points = [
      point("Denver, CO", "2024-01-01", 2000),
      point("Denver, CO", "2024-02-01", 2200),
    ];
    const text = summarizeResults(points, "median_rent", "period");
    expect(text).toBe("Denver, CO: $2,000 → $2,200 (up 10.0%).");
  });

  it("calls out a real peak that isn't the first or last point", () => {
    const points = [
      point("Denver, CO", "2024-01-01", 2000),
      point("Denver, CO", "2024-02-01", 2500),
      point("Denver, CO", "2024-03-01", 2100),
    ];
    const text = summarizeResults(points, "median_rent", "period");
    expect(text).toContain("peaked at $2,500 in Feb 2024");
  });

  it("treats a near-zero change as flat rather than up/down", () => {
    const points = [
      point("Denver, CO", "2024-01-01", 2000),
      point("Denver, CO", "2024-02-01", 2000.5),
    ];
    const text = summarizeResults(points, "median_rent", "period");
    expect(text).toContain("(flat");
  });

  it("handles multiple metros independently in trend mode", () => {
    const points = [
      point("Austin, TX", "2024-01-01", 400000),
      point("Austin, TX", "2024-02-01", 420000),
      point("Denver, CO", "2024-01-01", 500000),
      point("Denver, CO", "2024-02-01", 480000),
    ];
    const text = summarizeResults(points, "median_sale_price", "period");
    expect(text).toContain("Austin, TX: $400,000 → $420,000 (up 5.0%).");
    expect(text).toContain("Denver, CO: $500,000 → $480,000 (down 4.0%).");
  });
});
