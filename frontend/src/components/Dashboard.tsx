import { useEffect, useState } from "react";
import { fetchSnapshot } from "../api";
import type { MetroSnapshot } from "../types";
import { CorrelationChart } from "./CorrelationChart";
import { DistributionView } from "./DistributionView";
import { MetroCompareTable } from "./MetroCompareTable";

type View = "compare" | "correlate" | "distribution";

const VIEWS: { id: View; label: string }[] = [
  { id: "compare", label: "Compare" },
  { id: "correlate", label: "Correlate" },
  { id: "distribution", label: "Distribution" },
];

export function Dashboard() {
  const [snapshots, setSnapshots] = useState<MetroSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("compare");

  useEffect(() => {
    fetchSnapshot()
      .then(setSnapshots)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="empty-state">Loading snapshot…</p>;
  if (error) return <p className="error-banner">{error}</p>;

  return (
    <section className="dashboard">
      <p className="explanation browse-explanation">
        Every tracked metro's latest numbers, free to slice - no query limit, no model call.
      </p>
      <div className="dashboard-tabs" role="tablist">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            role="tab"
            aria-selected={view === v.id}
            className={view === v.id ? "active" : ""}
            onClick={() => setView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </div>

      {view === "compare" && <MetroCompareTable snapshots={snapshots} />}
      {view === "correlate" && <CorrelationChart snapshots={snapshots} />}
      {view === "distribution" && <DistributionView snapshots={snapshots} />}
    </section>
  );
}
