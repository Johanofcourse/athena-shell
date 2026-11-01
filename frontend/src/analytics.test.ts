import { describe, expect, it } from "vitest";
import {
  getMetricValue,
  linearRegression,
  pairSnapshotValues,
  pearsonCorrelation,
  rentToIncomePct,
  summaryStats,
  valuesForMetric,
  type XYPoint,
} from "./analytics";
import type { MetroSnapshot } from "./types";

function snapshot(metro: string, values: MetroSnapshot["values"]): MetroSnapshot {
  return { metro, state: "XX", values };
}

describe("pairSnapshotValues", () => {
  it("includes only metros with both metrics present", () => {
    const snapshots = [
      snapshot("Full, FU", { median_sale_price: 400000, natural_hazard_risk_score: 50 }),
      snapshot("MissingY, MY", { median_sale_price: 300000 }),
      snapshot("MissingX, MX", { natural_hazard_risk_score: 20 }),
    ];
    const points = pairSnapshotValues(snapshots, "median_sale_price", "natural_hazard_risk_score");
    expect(points).toEqual([{ metro: "Full, FU", x: 400000, y: 50 }]);
  });
});

describe("pearsonCorrelation", () => {
  it("is 1 for a perfectly increasing linear relationship", () => {
    const points: XYPoint[] = [
      { metro: "a", x: 1, y: 2 },
      { metro: "b", x: 2, y: 4 },
      { metro: "c", x: 3, y: 6 },
    ];
    expect(pearsonCorrelation(points)).toBeCloseTo(1, 10);
  });

  it("is -1 for a perfectly decreasing linear relationship", () => {
    const points: XYPoint[] = [
      { metro: "a", x: 1, y: 6 },
      { metro: "b", x: 2, y: 4 },
      { metro: "c", x: 3, y: 2 },
    ];
    expect(pearsonCorrelation(points)).toBeCloseTo(-1, 10);
  });

  it("is NaN when there are fewer than 2 points", () => {
    expect(pearsonCorrelation([{ metro: "a", x: 1, y: 2 }])).toBeNaN();
  });

  it("is NaN when one series has zero variance", () => {
    const points: XYPoint[] = [
      { metro: "a", x: 5, y: 1 },
      { metro: "b", x: 5, y: 2 },
      { metro: "c", x: 5, y: 3 },
    ];
    expect(pearsonCorrelation(points)).toBeNaN();
  });
});

describe("linearRegression", () => {
  it("recovers the exact slope/intercept of a noiseless line", () => {
    const points: XYPoint[] = [
      { metro: "a", x: 0, y: 3 },
      { metro: "b", x: 1, y: 5 },
      { metro: "c", x: 2, y: 7 },
    ];
    const fit = linearRegression(points);
    expect(fit.slope).toBeCloseTo(2, 10);
    expect(fit.intercept).toBeCloseTo(3, 10);
  });
});

describe("summaryStats", () => {
  it("returns null for an empty list", () => {
    expect(summaryStats([])).toBeNull();
  });

  it("computes mean/median/min/max/stdev for an odd-length list", () => {
    const stats = summaryStats([10, 20, 30]);
    expect(stats).toEqual({
      count: 3,
      mean: 20,
      median: 20,
      min: 10,
      max: 30,
      stdev: Math.sqrt(((10 - 20) ** 2 + (20 - 20) ** 2 + (30 - 20) ** 2) / 3),
    });
  });

  it("averages the two middle values for an even-length list's median", () => {
    const stats = summaryStats([10, 20, 30, 40]);
    expect(stats?.median).toBe(25);
  });
});

describe("valuesForMetric", () => {
  it("omits metros missing that metric", () => {
    const snapshots = [
      snapshot("Has, HA", { median_rent: 1500 }),
      snapshot("Lacks, LA", { median_sale_price: 300000 }),
    ];
    expect(valuesForMetric(snapshots, "median_rent")).toEqual([{ metro: "Has, HA", value: 1500 }]);
  });
});

describe("getMetricValue", () => {
  it("routes rent_to_income_pct through the derived ratio, not a direct lookup", () => {
    const s = snapshot("Austin, TX", { median_rent: 2000, median_household_income: 96000 });
    expect(getMetricValue(s, "rent_to_income_pct")).toBeCloseTo(25, 10);
  });

  it("falls back to a direct values lookup for every other metric", () => {
    const s = snapshot("Austin, TX", { median_sale_price: 450000 });
    expect(getMetricValue(s, "median_sale_price")).toBe(450000);
  });
});

describe("rentToIncomePct", () => {
  it("matches the backend's (rent * 12 / income) * 100 formula", () => {
    const s = snapshot("Austin, TX", { median_rent: 2000, median_household_income: 96000 });
    expect(rentToIncomePct(s)).toBeCloseTo(25, 10);
  });

  it("is undefined when either leg is missing", () => {
    expect(rentToIncomePct(snapshot("NoIncome, NI", { median_rent: 2000 }))).toBeUndefined();
    expect(rentToIncomePct(snapshot("NoRent, NR", { median_household_income: 96000 }))).toBeUndefined();
  });
});
