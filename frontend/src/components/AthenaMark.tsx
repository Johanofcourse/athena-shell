export function AthenaMark({ size = 48 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
      className="athena-mark"
    >
      <path d="M11 17 L13 6 L19 13 Z M37 17 L35 6 L29 13 Z" fill="currentColor" />
      <path
        d="M24 12 C15 12 10 19 10 28 C10 38 16 44 24 44 C32 44 38 38 38 28 C38 19 33 12 24 12 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      />
      <circle cx="18" cy="26" r="5" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="30" cy="26" r="5" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="18" cy="26" r="1.8" fill="var(--accent)" />
      <circle cx="30" cy="26" r="1.8" fill="var(--accent)" />
      <path d="M24 31 L21.5 36 L24 38 L26.5 36 Z" fill="currentColor" />
    </svg>
  );
}
