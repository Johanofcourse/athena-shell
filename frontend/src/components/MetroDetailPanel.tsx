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
      metro.has_rent_data
        ? fetchMetroSeries(metro.id, "median_rent", "overall")
        : Promise.resolve([]),
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
                <TrendChart points={salePoints} />
              </>
            )}
            {metro.has_rent_data ? (
              <>
                <h3>Median rent</h3>
                <TrendChart points={rentPoints} />
              </>
            ) : (
              <p className="empty-state">
                No rent data for {metro.canonical_name} - Apartment List only publishes this at a
                larger combined metro level for this area.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
