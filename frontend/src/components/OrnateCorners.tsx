import { CornerFlourish } from "./CornerFlourish";

// Four mirrored copies of the same scroll, one per corner - shared
// between the search bar and the map, the two places with an ornate
// double-ruled frame, so the convention stays consistent rather than
// building a one-off for each. The parent needs position: relative;
// CSS (.corner-flourish[data-corner=...]) positions and mirrors each
// instance - this component just places the four, it doesn't know the
// orientation math itself.
export function OrnateCorners({ size = 44 }: { size?: number }) {
  return (
    <>
      <span className="corner-flourish-slot" data-corner="top-left">
        <CornerFlourish size={size} />
      </span>
      <span className="corner-flourish-slot" data-corner="top-right">
        <CornerFlourish size={size} />
      </span>
      <span className="corner-flourish-slot" data-corner="bottom-left">
        <CornerFlourish size={size} />
      </span>
      <span className="corner-flourish-slot" data-corner="bottom-right">
        <CornerFlourish size={size} />
      </span>
    </>
  );
}
