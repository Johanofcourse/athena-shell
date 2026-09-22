import type { Listing } from "../types";
import { ListingCard } from "./ListingCard";

interface Props {
  listings: Listing[];
  onSelect: (id: string) => void;
}

export function ResultsList({ listings, onSelect }: Props) {
  if (listings.length === 0) {
    return <p className="empty-state">No listings match that query.</p>;
  }

  return (
    <div className="results-grid">
      {listings.map((listing) => (
        <ListingCard key={listing.id} listing={listing} onSelect={onSelect} />
      ))}
    </div>
  );
}
