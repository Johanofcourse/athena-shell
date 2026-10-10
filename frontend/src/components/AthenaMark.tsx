// The owl of Athena, drawn as pure single-weight contour - the technique
// of Attic red-figure vase painting (and, later, Flaxman's neoclassical
// line engravings) rather than a filled icon. Every stroke is the same
// weight, nothing is shaded, and the only fill is the pupils - the one
// place a classical vase painter would still use a solid accent. A quiet
// signature mark (see docs/ROADMAP.md redesign notes), not a hero image.
export function AthenaMark({ size = 56 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 56 56"
      aria-hidden="true"
      className="athena-mark"
    >
      <path
        d="M14 20 C11 14 12 8 16 5 C16.5 9 18 12 20 14 Z
           M42 20 C45 14 44 8 40 5 C39.5 9 38 12 36 14 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M28 14 C18 14 12 22 12 32 C12 42 18 50 28 50 C38 50 44 42 44 32 C44 22 38 14 28 14 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <circle cx="21" cy="30" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="35" cy="30" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="21" cy="30" r="1.6" fill="var(--accent)" />
      <circle cx="35" cy="30" r="1.6" fill="var(--accent)" />
      <path d="M28 34 L25.5 39 L28 41.5 L30.5 39 Z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path
        d="M19 44 C21 47 25 48.5 28 48.5 C31 48.5 35 47 37 44"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
      />
    </svg>
  );
}
