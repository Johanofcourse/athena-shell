import { useState } from "react";
import coltonMap from "../assets/colton-us-map-1870s.jpg";
import { METRO_MAP_COORDINATES } from "../mapCoordinates";
import type { Metro } from "../types";

// The map image's own aspect ratio (2400x1457) - the image wrapper is
// locked to this via CSS so percentage pin coordinates (calibrated
// against the image's pixels, see mapCoordinates.ts) always land in the
// right place, with no object-fit letterboxing to account for.
const MAP_ASPECT_RATIO = "2400 / 1457";

// Near the map's top edge, an "above the pin" callout would render
// partly off-canvas - flip it below the pin instead past this point.
const FLIP_CALLOUT_BELOW_ABOVE_Y_PCT = 15;

interface Props {
  metros: Metro[];
  onSelect: (metro: Metro) => void;
}

export function UsMetroMap({ metros, onSelect }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  // A click selects a pin (shows its name in a callout) rather than
  // navigating straight to the metro detail panel - a second click on
  // the pin or the callout itself is what actually navigates. See the
  // .metro-map-callout CSS for why: dense clusters (south Florida) sit
  // close enough that an imprecise first click landing on the wrong
  // pin is a one-tap-to-correct mistake instead of an immediate wrong
  // navigation.
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  function handlePinClick(metro: Metro) {
    if (confirmingId === metro.id) {
      onSelect(metro);
      setConfirmingId(null);
    } else {
      setConfirmingId(metro.id);
    }
  }

  const confirmingMetro = metros.find((m) => m.id === confirmingId) ?? null;
  const confirmingCoords = confirmingMetro ? METRO_MAP_COORDINATES[confirmingMetro.id] : null;

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
        <div
          className="metro-map-image-wrap"
          style={{ aspectRatio: MAP_ASPECT_RATIO }}
          onClick={() => setConfirmingId(null)}
        >
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
                data-confirming={confirmingId === metro.id}
                onClick={(e) => {
                  e.stopPropagation();
                  handlePinClick(metro);
                }}
                onMouseEnter={() => setHoveredId(metro.id)}
                onMouseLeave={() => setHoveredId((id) => (id === metro.id ? null : id))}
                aria-label={metro.canonical_name}
                title={metro.canonical_name}
              />
            );
          })}
          {confirmingMetro && confirmingCoords && (
            <button
              type="button"
              className="metro-map-callout"
              data-flip={confirmingCoords[1] < FLIP_CALLOUT_BELOW_ABOVE_Y_PCT}
              style={{ left: `${confirmingCoords[0]}%`, top: `${confirmingCoords[1]}%` }}
              onClick={(e) => {
                e.stopPropagation();
                onSelect(confirmingMetro);
                setConfirmingId(null);
              }}
            >
              <span className="metro-map-callout-name">{confirmingMetro.canonical_name}</span>
              <span className="metro-map-callout-hint">Tap again to view</span>
            </button>
          )}
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
