import type { Listing, ListingDetail, QueryResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function fetchListings(limit = 50): Promise<Listing[]> {
  return request(`/listings?limit=${limit}`);
}

export function fetchListing(id: string): Promise<ListingDetail> {
  return request(`/listings/${id}`);
}

export function runQuery(query: string): Promise<QueryResponse> {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
