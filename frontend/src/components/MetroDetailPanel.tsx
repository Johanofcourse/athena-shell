import { useEffect, useState } from "react";
import { fetchMetroSeries } from "../api";
import type { MarketMetricPoint, Metro } from "../types";
import { TrendChart } from "./TrendChart";

interface Props {
  metro: Metro;
  onClose: () => void;
}

export function MetroDetailPanel({ metro, onClose }: Props) {
  const [salePoints, setSalePoints] = useState<MarketMetricPoint[]>([]);
  const [rentPoints, setRentPoints] = useState<MarketMetricPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      metro.has_sale_data ? fetchMetroSeries(metro.id, "median_sale_price") : Promise.resolve([]),
      // Always fetched, even when has_rent_data is false: the API falls
      // back to Census median_gross_rent for the 10 metro-division metros
      // Apartment List doesn't cover, so this can still come back with
      // real (flagged) data - see MetroDetailPanel's render below.
      fetchMetroSeries(metro.id, "median_rent", "overall"),
    ])
      .then(([sale, rent]) => {
        setSalePoints(sale);
        setRentPoints(rent);
      })
      .finally(() => setLoading(false));
  }, [metro]);

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h2>{metro.canonical_name}</h2>

        {loading ? (
          <p>Loading…</p>
        ) : (
          <>
            {metro.has_sale_data && (
              <>
                <h3>Median sale price</h3>
                <TrendChart points={salePoints} metric="median_sale_price" />
              </>
            )}
            {rentPoints.length > 0 ? (
              <>
                <h3>Median rent</h3>
                {!metro.has_rent_data && (
                  <p className="empty-state">
                    Apartment List doesn't publish rent for {metro.canonical_name} at this
                    granularity - showing Census ACS median gross rent instead, a related but
                    methodologically different measure.
                  </p>
                )}
                <TrendChart points={rentPoints} metric="median_rent" />
              </>
            ) : (
              <p className="empty-state">
                No rent data for {metro.canonical_name} - Apartment List only publishes this at a
                larger combined metro level for this area, and no Census fallback is available
                either.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
