import { useRef, useState } from "react";
import { TransformComponent, TransformWrapper, type ReactZoomPanPinchContentRef } from "react-zoom-pan-pinch";
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
  // A click selects a pin (shows its name in a callout) rather than
  // navigating straight to the metro detail panel - a second click on
  // the pin or the callout itself is what actually navigates. See the
  // .metro-map-callout CSS for why: dense clusters (south Florida) sit
  // close enough that an imprecise first click landing on the wrong
  // pin is a one-tap-to-correct mistake instead of an immediate wrong
  // navigation.
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);

  function handlePinClick(metro: Metro) {
    if (confirmingId === metro.id) {
      onSelect(metro);
      setConfirmingId(null);
      // Scoped to this component's own zoom/pan state (see the
      // TransformWrapper below) - resetting it here is a real reset of
      // something we actually control, unlike the native-pinch-zoom
      // reset this replaced (see git history: toggling the viewport
      // meta's max-scale, the standard trick for that, turned out not
      // to work on a real iPhone - modern iOS Safari ignores JS-driven
      // zoom changes, deliberately, for accessibility). Zooming the map
      // itself instead of the whole page means the metro detail panel
      // that opens next was never going to inherit a pinched-in zoom
      // level in the first place; this just leaves the map ready to
      // browse again at 1x next time someone opens it.
      transformRef.current?.resetTransform();
    } else {
      setConfirmingId(metro.id);
    }
  }

  const confirmingMetro = metros.find((m) => m.id === confirmingId) ?? null;

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
        {/* Pinch/pan/zoom scoped to just this component, not the page -
            Johan: zooming the whole page via native pinch-zoom then
            tapping a pin left the metro detail panel rendered at that
            same zoomed-in level ("the graph is gigantic"). A self-
            contained zoom here means the rest of the page, including
            whatever opens next, is never part of what's zoomed -
            there's nothing to reset because nothing outside the map
            itself was ever magnified. wheel zoom is off so scrolling
            the page with a mouse over the map behaves normally;
            pinch/double-click/drag-to-pan still work for getting a
            closer look at a dense cluster before picking a pin. */}
        {/* The callout below is a sibling of TransformWrapper, inside
            this relatively-positioned wrapper specifically (not
            .metro-map-canvas as a whole) - anchoring it to the map area
            alone, rather than the canvas including the title, is what
            lets it sit right at the top of the map without overlapping
            the title text above it. */}
        <div className="metro-map-zoom-area">
          <TransformWrapper
            ref={transformRef}
            initialScale={1}
            minScale={1}
            maxScale={6}
            centerOnInit
            wheel={{ disabled: true }}
            doubleClick={{ mode: "zoomIn" }}
          >
            <TransformComponent wrapperStyle={{ width: "100%" }} contentStyle={{ width: "100%" }}>
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
              </div>
            </TransformComponent>
          </TransformWrapper>
          {/* Deliberately rendered OUTSIDE TransformWrapper, not
              anchored to the pin's own (zoomed/panned) position like
              the first version of this was - Johan: zoomed into south
              Florida and picked Orlando, and the callout naming it was
              clipped by the map's own frame, since it inherited the
              same pan/zoom transform and the same overflow:hidden
              clipping as the pins do. A fixed banner over the top of
              the map is never subject to either, regardless of how far
              in someone has zoomed or where on the map the pin they
              picked actually is. */}
          {confirmingMetro && (
            <button
              type="button"
              className="metro-map-callout"
              onClick={(e) => {
                e.stopPropagation();
                onSelect(confirmingMetro);
                setConfirmingId(null);
                transformRef.current?.resetTransform();
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
