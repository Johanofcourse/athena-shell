export type ListingStatus = "active" | "pending" | "sold" | "off_market";

export type EventType =
  | "listed"
  | "price_change"
  | "status_change"
  | "relisted"
  | "delisted"
  | "sold";

export interface ListingEvent {
  event_type: EventType;
  event_date: string;
  price: number | null;
  status: ListingStatus | null;
  notes: string | null;
}

export interface Listing {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  first_listed_date: string;
  last_event_date: string;
  original_price: number;
  current_price: number;
  price_drop_amount: number;
  price_drop_pct: number;
  status: ListingStatus;
  days_on_market: number;
  total_days_on_market: number;
  relist_count: number;
}

export interface ListingDetail extends Listing {
  events: ListingEvent[];
}

export interface QueryFilters {
  min_price?: number | null;
  max_price?: number | null;
  city?: string | null;
  state?: string | null;
  property_type?: string | null;
  bedrooms_min?: number | null;
  bathrooms_min?: number | null;
  min_price_drop_pct?: number | null;
  min_price_drop_amount?: number | null;
  min_days_on_market?: number | null;
  max_days_on_market?: number | null;
  min_relist_count?: number | null;
  status?: ListingStatus | null;
  sort_by?: string | null;
  sort_order?: string | null;
  limit: number;
}

export interface QueryResponse {
  filters: QueryFilters;
  explanation: string;
  results: Listing[];
}
