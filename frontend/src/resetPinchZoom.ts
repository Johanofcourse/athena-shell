/** Johan: zooming into the map on mobile, then tapping a pin, leaves the
 * metro detail panel that opens rendered at that same pinched-in zoom
 * level - "the graph is gigantic." There's no direct JS API to read or
 * set the browser's native pinch-zoom level. Briefly tightening the
 * viewport meta tag's max-scale is the standard workaround (widely used
 * for exactly this "a modal opened at an awkward zoom level" problem) -
 * mobile Safari/Chrome snap the visual viewport back to within the new
 * constraint, and restoring the original content right after means
 * pinch-zoom still works normally afterward; this is a momentary nudge,
 * not a permanent zoom lock. Only emulator-testable up to a point - the
 * actual snap-back behavior is a real-device thing. */
export function resetPinchZoom(): void {
  const meta = document.querySelector('meta[name="viewport"]');
  const original = meta?.getAttribute("content");
  if (!meta || !original) return;
  meta.setAttribute("content", `${original}, maximum-scale=1`);
  window.setTimeout(() => {
    meta.setAttribute("content", original);
  }, 300);
}
