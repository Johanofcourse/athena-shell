import type { Metro } from "../types";

interface Props {
  metros: Metro[];
  onSelect: (metro: Metro) => void;
}

export function MetroGrid({ metros, onSelect }: Props) {
  return (
    <div className="metro-grid">
      {metros.map((metro) => (
        <button key={metro.id} className="metro-card" onClick={() => onSelect(metro)}>
          <div className="address">{metro.canonical_name}</div>
          <div className="metro-badges">
            {metro.has_sale_data && <span className="status-badge status-active">Sale data</span>}
            {metro.has_rent_data && <span className="status-badge status-sold">Rent data</span>}
          </div>
        </button>
      ))}
    </div>
  );
}
