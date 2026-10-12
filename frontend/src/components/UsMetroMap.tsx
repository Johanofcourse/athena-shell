import { useState } from "react";
import coltonMap from "../assets/colton-us-map-1870s.jpg";
import { METRO_MAP_COORDINATES } from "../mapCoordinates";
import type { Metro } from "../types";

// The map image's own aspect ratio (2400x1457) - the image wrapper is
// locked to this via CSS so percentage pin coordinates (calibrated
// against the image's pixels, see mapCoordinates.ts) always land in the
// right place, with no object-fit letterboxing to account for.
const MAP_ASPECT_RATIO = "2400 / 1457";

interface Props {
  metros: Metro[];
  onSelect: (metro: Metro) => void;
}

export function UsMetroMap({ metros, onSelect }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="metro-map-layout">
      <div className="metro-map-canvas">
        {/* A title cartouche, same convention every map on
            thoughtco.com/maps-of-ancient-greece uses - the reference
            Johan sent for this redesign. */}
        <p className="metro-map-title">
          <span className="metro-map-title-rule" aria-hidden="true" />
          The United States
          <span className="metro-map-title-rule" aria-hidden="true" />
        </p>
        <div className="metro-map-image-wrap" style={{ aspectRatio: MAP_ASPECT_RATIO }}>
          <img
            src={coltonMap}
            alt="An 1870s Colton's atlas map of the United States"
            className="metro-map-image"
            draggable={false}
          />
          {metros.map((metro) => {
            const coords = METRO_MAP_COORDINATES[metro.id];
            if (!coords) return null;
            const [xPct, yPct] = coords;
            return (
              <button
                key={metro.id}
                type="button"
                className="metro-map-pin"
                style={{ left: `${xPct}%`, top: `${yPct}%` }}
                data-hovered={hoveredId === metro.id}
                onClick={() => onSelect(metro)}
                onMouseEnter={() => setHoveredId(metro.id)}
                onMouseLeave={() => setHoveredId((id) => (id === metro.id ? null : id))}
                aria-label={metro.canonical_name}
                title={metro.canonical_name}
              />
            );
          })}
        </div>
      </div>

      <details className="metro-list-toggle">
        <summary className="intro-label">Top 50 metros — basic info</summary>
        <ul className="metro-list">
          {metros.map((metro) => (
            <li key={metro.id}>
              <button
                className="metro-list-item"
                data-hovered={hoveredId === metro.id}
                onClick={() => onSelect(metro)}
                onMouseEnter={() => setHoveredId(metro.id)}
                onMouseLeave={() => setHoveredId((id) => (id === metro.id ? null : id))}
              >
                <span className="metro-list-name">{metro.canonical_name}</span>
                <span className="metro-list-badges">
                  <span className="metro-cell" data-available={metro.has_sale_data} title={metro.has_sale_data ? "Sale data" : "No sale data"}>Sale</span>
                  <span className="metro-cell" data-available={metro.has_rent_data} title={metro.has_rent_data ? "Rent data" : "No rent data"}>Rent</span>
                  <span className="metro-cell" data-available={metro.has_income_data} title={metro.has_income_data ? "Income data" : "No income data"}>Income</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
