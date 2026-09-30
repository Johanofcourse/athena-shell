export type MetricName =
  | "median_sale_price"
  | "median_days_on_market"
  | "homes_sold"
  | "new_listings"
  | "active_listings"
  | "pending_sales"
  | "median_price_per_sqft"
  | "price_drop_count"
  | "price_drop_pct_avg"
  | "pct_active_with_price_drop"
  | "homes_sold_with_price_drop"
  | "total_delistings"
  | "total_relistings"
  | "share_delisted_pct"
  | "share_relisted_pct"
  | "median_rent"
  | "vacancy_rate"
  | "time_on_market_days"
  | "median_household_income"
  | "rent_to_income_pct"
  | "unemployment_rate"
  | "median_gross_rent"
  | "mortgage_rate_30yr_fixed"
  | "mortgage_rate_15yr_fixed"
  | "mortgage_rate_5_1_arm";

export interface Metro {
  id: string;
  canonical_name: string;
  state: string;
  has_sale_data: boolean;
  has_rent_data: boolean;
  has_income_data: boolean;
  census_gross_rent_county: string | null;
}

export interface MarketMetricPoint {
  metro: string;
  period: string;
  value: number;
}

export interface MarketQueryFilters {
  metros: string[];
  metric: MetricName;
  bed_size: string | null;
  start_period: string | null;
  end_period: string | null;
  sort_by: "period" | "value";
  sort_order: "asc" | "desc";
  limit: number;
  unsupported_aspects: string[];
}

export interface MarketQueryResponse {
  filters: MarketQueryFilters;
  explanation: string;
  unmatched_metros: string[];
  no_data_metros: string[];
  approximated_metros: string[];
  results: MarketMetricPoint[];
}

export interface ConversationTurn {
  query: string;
  filters: MarketQueryFilters;
}
