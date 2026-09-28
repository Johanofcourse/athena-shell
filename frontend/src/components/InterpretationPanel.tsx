import type { MarketQueryFilters } from "../types";

interface Props {
  filters: MarketQueryFilters;
}

const FIELD_LABELS: Record<string, string> = {
  metros: "Metros",
  metric: "Metric",
  bed_size: "Bed size",
  start_period: "Start period",
  end_period: "End period",
  sort_by: "Sort by",
  sort_order: "Sort order",
  limit: "Limit",
  unsupported_aspects: "Flagged as unsupported",
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  return String(value);
}

/** Shows the exact structured tool-call arguments DeepSeek produced for
 * this query - not a paraphrase, the real thing the API returned. The
 * whole point of the tool-calling architecture is that this is always
 * knowable and auditable; this panel is where that becomes visible
 * instead of just being true in the abstract. */
export function InterpretationPanel({ filters }: Props) {
  const fields: [keyof typeof FIELD_LABELS, unknown][] = [
    ["metros", filters.metros],
    ["metric", filters.metric],
    ["bed_size", filters.bed_size],
    ["start_period", filters.start_period],
    ["end_period", filters.end_period],
    ["sort_by", filters.sort_by],
    ["sort_order", filters.sort_order],
    ["limit", filters.limit],
    ["unsupported_aspects", filters.unsupported_aspects],
  ];

  return (
    <details className="interpretation-panel">
      <summary>How this was interpreted</summary>
      <dl>
        {fields.map(([key, value]) => (
          <div className="interpretation-row" key={key}>
            <dt>{FIELD_LABELS[key]}</dt>
            <dd>{formatValue(value)}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
