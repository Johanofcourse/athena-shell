import type { Listing } from "../types";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const STATUS_LABEL: Record<Listing["status"], string> = {
  active: "Active",
  pending: "Pending",
  sold: "Sold",
  off_market: "Off market",
};

interface Props {
  listing: Listing;
  onSelect: (id: string) => void;
}

export function ListingCard({ listing, onSelect }: Props) {
  const hasDrop = listing.price_drop_amount > 0;

  return (
    <button className="listing-card" onClick={() => onSelect(listing.id)}>
      <div className="listing-card-header">
        <span className={`status-badge status-${listing.status}`}>
          {STATUS_LABEL[listing.status]}
        </span>
        <span className="dom">{listing.days_on_market}d on market</span>
      </div>
      <div className="address">{listing.address}</div>
      <div className="location">
        {listing.city}, {listing.state} {listing.zip_code}
      </div>
      <div className="price-row">
        <span className="price">{currency.format(listing.current_price)}</span>
        {hasDrop && (
          <span className="price-drop">
            -{currency.format(listing.price_drop_amount)} ({listing.price_drop_pct.toFixed(1)}%)
          </span>
        )}
      </div>
      <div className="facts">
        {listing.bedrooms} bd · {listing.bathrooms} ba · {listing.sqft.toLocaleString()} sqft
      </div>
      {listing.relist_count > 0 && (
        <div className="relist-flag">Relisted {listing.relist_count}×</div>
      )}
    </button>
  );
}
