import type { MetricName } from "./types";

// Every metric the Insights dashboard can show - the 14 the backend's
// /analytics/snapshot ships (backend/app/routers/analytics.py's
// SNAPSHOT_METRICS, same order) plus rent_to_income_pct, the one ratio
// the frontend derives itself rather than the backend shipping directly
// (see analytics.ts's getMetricValue/rentToIncomePct).
export const DASHBOARD_METRICS: MetricName[] = [
  "median_sale_price",
  "median_days_on_market",
  "active_listings",
  "pct_active_with_price_drop",
  "median_price_per_sqft",
  "median_rent",
  "vacancy_rate",
  "median_household_income",
  "rent_to_income_pct",
  "unemployment_rate",
  "mean_commute_minutes",
  "median_property_tax",
  "total_population",
  "house_price_index",
  "natural_hazard_risk_score",
];

export const METRIC_LABELS: Record<MetricName, string> = {
  median_sale_price: "Median sale price",
  median_days_on_market: "Days on market",
  homes_sold: "Homes sold",
  new_listings: "New listings",
  active_listings: "Active listings",
  pending_sales: "Pending sales",
  median_price_per_sqft: "Price per sq ft",
  price_drop_count: "Price drop count",
  price_drop_pct_avg: "Avg. price drop",
  pct_active_with_price_drop: "% listings with price drop",
  homes_sold_with_price_drop: "Homes sold with price drop",
  total_delistings: "Total delistings",
  total_relistings: "Total relistings",
  share_delisted_pct: "% delisted",
  share_relisted_pct: "% relisted",
  median_rent: "Median rent",
  vacancy_rate: "Vacancy rate",
  time_on_market_days: "Time on market (days)",
  median_household_income: "Household income",
  rent_to_income_pct: "Rent-to-income ratio",
  unemployment_rate: "Unemployment rate",
  house_price_index: "House price index",
  mean_commute_minutes: "Mean commute (min)",
  median_property_tax: "Property tax",
  natural_hazard_risk_score: "Natural hazard risk score",
  total_population: "Population",
  median_gross_rent: "Median gross rent (Census)",
  mortgage_rate_30yr_fixed: "30yr fixed mortgage rate",
  mortgage_rate_15yr_fixed: "15yr fixed mortgage rate",
  mortgage_rate_5_1_arm: "5/1 ARM mortgage rate",
};
