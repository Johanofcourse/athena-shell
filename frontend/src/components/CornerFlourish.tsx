// A single baroque scroll - a volute (the classic spiral curl) with one
// leaf branching off its stem - drawn as pure single-weight line, the
// same technique as AthenaMark and CompassRose. Deliberately simpler
// than a full rococo cartouche (see the reference Johan sent,
// centurylibrary.com's engraved border): that level of dense,
// continuous scrollwork is a real hand-engraving craft, not something
// worth faking badly in raw SVG coordinates. One clean scroll, mirrored
// into all four corners by the caller via CSS transforms, reads as a
// real decorative flourish without pretending to be something it isn't.
export function CornerFlourish({ size = 44 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 68 68" aria-hidden="true" className="corner-flourish">
      <path
        d="M12.8,38.0 L13.6,34.1 L15.1,30.5 L17.2,27.3 L19.8,24.7 L22.8,22.6 L26.1,21.2 L29.5,20.4
           L32.9,20.3 L36.2,20.9 L39.2,22.0 L41.9,23.6 L44.2,25.7 L46.0,28.1 L47.3,30.7 L48.0,33.5
           L48.2,36.2 L47.8,38.9 L47.0,41.3 L45.8,43.5 L44.2,45.4 L42.3,46.9 L40.3,47.9 L38.2,48.6
           L36.1,48.7 L34.0,48.5 L32.1,47.9 L30.4,47.0 L29.0,45.9 L27.9,44.5 L27.1,43.0 L26.7,41.4
           L26.5,39.9 L26.7,38.5 L27.1,37.1 L27.8,36.0 L28.6,35.0 L29.6,34.3 L30.6,33.9 L31.6,33.6
           L32.6,33.6 L33.5,33.8 L34.2,34.1 L34.9,34.6 L35.3,35.2 L35.6,35.7 L35.8,36.3 L35.8,36.9
           L35.7,37.3 L35.4,37.7 L35.2,38.0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12.8,38.0 C8,44 5,52 5,62" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path
        d="M8,50 C2,48 -1,42 1,36 C6,39 9,45 8,50 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
    </svg>
  );
}
