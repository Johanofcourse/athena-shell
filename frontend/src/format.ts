import type { MetricName } from "./types";

// median_sale_price/median_rent are whole dollars; median_price_per_sqft
// carries cents (e.g. 213.4) - one formatter handles both correctly.
const CURRENCY_METRICS = new Set<MetricName>([
  "median_sale_price",
  "median_rent",
  "median_price_per_sqft",
  "median_household_income",
  "median_gross_rent",
]);

// Stored as a 0-1 fraction (0.0848 = 8.48%), unlike the metrics below.
const FRACTION_PERCENT_METRICS = new Set<MetricName>(["vacancy_rate"]);

// Already stored as a percent number (6.76 meaning 6.76%), not a fraction.
const PERCENT_METRICS = new Set<MetricName>([
  "price_drop_pct_avg",
  "pct_active_with_price_drop",
  "share_delisted_pct",
  "share_relisted_pct",
  "rent_to_income_pct",
]);

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
const fractionPercentFormatter = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 });
const plainNumberFormatter = new Intl.NumberFormat("en-US");

export function formatMetricValue(metric: MetricName, value: number): string {
  if (CURRENCY_METRICS.has(metric)) return currencyFormatter.format(value);
  if (FRACTION_PERCENT_METRICS.has(metric)) return fractionPercentFormatter.format(value);
  if (PERCENT_METRICS.has(metric)) return `${value.toFixed(1)}%`;
  // homes_sold, days-on-market, listing counts, etc. - a plain comma-grouped number.
  return plainNumberFormatter.format(value);
}
