import { describe, expect, it } from "vitest";
import { formatMetricValue } from "./format";

describe("formatMetricValue", () => {
  it("formats currency metrics with a dollar sign and thousands commas", () => {
    expect(formatMetricValue("median_sale_price", 580000)).toBe("$580,000");
    expect(formatMetricValue("median_rent", 2343)).toBe("$2,343");
  });

  it("keeps up to two decimal places for price-per-sqft without padding whole numbers", () => {
    expect(formatMetricValue("median_price_per_sqft", 213.4)).toBe("$213.4");
    expect(formatMetricValue("median_price_per_sqft", 213)).toBe("$213");
  });

  it("formats the two new Census currency metrics the same way", () => {
    expect(formatMetricValue("median_household_income", 100431)).toBe("$100,431");
    expect(formatMetricValue("median_gross_rent", 1800)).toBe("$1,800");
  });

  it("formats a 0-1 fraction metric as a percent", () => {
    expect(formatMetricValue("vacancy_rate", 0.0848)).toBe("8.5%");
  });

  it("formats an already-percent metric with a plain % suffix", () => {
    expect(formatMetricValue("price_drop_pct_avg", 6.76)).toBe("6.8%");
    expect(formatMetricValue("rent_to_income_pct", 24.5)).toBe("24.5%");
  });

  it("formats national mortgage rates as a plain percent, same as rent_to_income_pct", () => {
    expect(formatMetricValue("mortgage_rate_30yr_fixed", 6.71)).toBe("6.7%");
    expect(formatMetricValue("mortgage_rate_15yr_fixed", 5.89)).toBe("5.9%");
    expect(formatMetricValue("mortgage_rate_5_1_arm", 6.06)).toBe("6.1%");
  });

  it("formats a plain count with thousands commas and no prefix/suffix", () => {
    expect(formatMetricValue("homes_sold", 12345)).toBe("12,345");
  });
});
