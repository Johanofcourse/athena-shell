import type { ListingDetail } from "../types";
import { ListingHistoryChart } from "./ListingHistoryChart";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const EVENT_LABEL: Record<string, string> = {
  listed: "Listed",
  price_change: "Price change",
  status_change: "Status change",
  relisted: "Relisted",
  delisted: "Delisted",
  sold: "Sold",
};

interface Props {
  listing: ListingDetail | null;
  loading: boolean;
  onClose: () => void;
}

export function ListingDetailPanel({ listing, loading, onClose }: Props) {
  if (!loading && !listing) return null;

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose} aria-label="Close">
          ×
        </button>
        {loading || !listing ? (
          <p>Loading…</p>
        ) : (
          <>
            <h2>{listing.address}</h2>
            <p className="location">
              {listing.city}, {listing.state} {listing.zip_code}
            </p>

            <div className="stat-grid">
              <div>
                <span className="stat-label">Current price</span>
                <span className="stat-value">{currency.format(listing.current_price)}</span>
              </div>
              <div>
                <span className="stat-label">Original price</span>
                <span className="stat-value">{currency.format(listing.original_price)}</span>
              </div>
              <div>
                <span className="stat-label">Days on market</span>
                <span className="stat-value">{listing.days_on_market}</span>
              </div>
              <div>
                <span className="stat-label">Relisted</span>
                <span className="stat-value">{listing.relist_count}×</span>
              </div>
            </div>

            <ListingHistoryChart events={listing.events} />

            <h3>Timeline</h3>
            <ul className="timeline">
              {listing.events.map((event, i) => (
                <li key={i}>
                  <span className="timeline-date">{event.event_date}</span>
                  <span className="timeline-type">{EVENT_LABEL[event.event_type]}</span>
                  {event.price != null && (
                    <span className="timeline-price">{currency.format(event.price)}</span>
                  )}
                  {event.notes && <span className="timeline-notes">{event.notes}</span>}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
