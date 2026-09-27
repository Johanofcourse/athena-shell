import type { MarketMetricPoint, MarketQueryResponse, Metro, MetricName } from "./types";

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

export function fetchMetros(): Promise<Metro[]> {
  return request("/metros");
}

export function fetchMetroSeries(
  metroId: string,
  metric: MetricName,
  bedSize?: string,
): Promise<MarketMetricPoint[]> {
  const params = new URLSearchParams({ metric });
  if (bedSize) params.set("bed_size", bedSize);
  return request(`/metros/${metroId}/series?${params.toString()}`);
}

export function runQuery(query: string): Promise<MarketQueryResponse> {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
