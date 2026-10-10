// A compass rose, drawn in the same pure single-contour line style as
// AthenaMark - the antique-cartography fixture this map borrows its
// whole visual language from (see thoughtco.com/maps-of-ancient-greece,
// the reference Johan sent). Eight spokes (four long cardinal, four
// short diagonal), a ring, and a small arrow at true north - understated
// rather than an ornate filled star, consistent with this project's
// "quiet signature" restraint elsewhere. The tiny owl at the center
// is the one deliberate tie back to the portrait: a real integration
// of the Athena motif into the map itself, not a second decoration
// competing with it.
export function CompassRose({ size = 72 }: { size?: number }) {
  const spokes = [0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
    const long = deg % 90 === 0;
    const r1 = 10;
    const r2 = long ? 34 : 24;
    const rad = (deg * Math.PI) / 180;
    // 0deg = north = up, so x uses sin, y uses -cos.
    const x1 = 50 + r1 * Math.sin(rad);
    const y1 = 50 - r1 * Math.cos(rad);
    const x2 = 50 + r2 * Math.sin(rad);
    const y2 = 50 - r2 * Math.cos(rad);
    return { deg, x1, y1, x2, y2 };
  });

  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true" className="compass-rose">
      <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="1" />
      {spokes.map((s) => (
        <line key={s.deg} x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} stroke="currentColor" strokeWidth="1" />
      ))}
      {/* North arrowhead - the one spoke that gets a real tip, same
          convention every antique compass rose uses to mark true north. */}
      <path d="M50 10 L45 22 L50 18 L55 22 Z" fill="currentColor" />
      {/* The owl, small and simplified for its size here - same facial
          structure as AthenaMark, fewer strokes. */}
      <circle cx="50" cy="50" r="9" fill="none" stroke="currentColor" strokeWidth="1" />
      <circle cx="46.5" cy="49" r="2" fill="none" stroke="currentColor" strokeWidth="0.8" />
      <circle cx="53.5" cy="49" r="2" fill="none" stroke="currentColor" strokeWidth="0.8" />
      <circle cx="46.5" cy="49" r="0.6" fill="var(--accent)" />
      <circle cx="53.5" cy="49" r="0.6" fill="var(--accent)" />
      <path d="M50 51.5 L48.8 54 L50 55.2 L51.2 54 Z" fill="none" stroke="currentColor" strokeWidth="0.7" />
    </svg>
  );
}
