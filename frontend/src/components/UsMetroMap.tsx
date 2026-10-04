import { geoAlbersUsa } from "d3-geo";
import { useState } from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
// us-atlas ships real Census TIGER/Line-derived topology - the same
// government-source instinct as every data source in this project,
// applied to the map itself. Raw (non-Albers-pre-projected) file, so
// react-simple-maps can project both the state outlines and the metro
// markers through the same geoAlbersUsa projection - using the
// pre-projected variant here would silently misalign the two.
import usStatesTopology from "us-atlas/states-10m.json?url";
import type { Metro } from "../types";

interface Props {
  metros: Metro[];
  onSelect: (metro: Metro) => void;
}

export function UsMetroMap({ metros, onSelect }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="metro-map-layout">
      <div className="metro-map-canvas">
        <ComposableMap projection={geoAlbersUsa()} projectionConfig={{ scale: 900 }}>
          <Geographies geography={usStatesTopology}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography key={geo.rsmKey} geography={geo} className="metro-map-state" tabIndex={-1} />
              ))
            }
          </Geographies>
          {metros.map((metro) => (
            <Marker
              key={metro.id}
              coordinates={[metro.longitude, metro.latitude]}
              onClick={() => onSelect(metro)}
              onMouseEnter={() => setHoveredId(metro.id)}
              onMouseLeave={() => setHoveredId((id) => (id === metro.id ? null : id))}
            >
              <circle
                r={hoveredId === metro.id ? 7 : 5}
                className="metro-map-pin"
                data-hovered={hoveredId === metro.id}
              >
                <title>{metro.canonical_name}</title>
              </circle>
            </Marker>
          ))}
        </ComposableMap>
      </div>

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
                {metro.has_sale_data && <span className="status-badge status-active">Sale</span>}
                {metro.has_rent_data && <span className="status-badge status-sold">Rent</span>}
                {metro.has_income_data && <span className="status-badge status-income">Income</span>}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
