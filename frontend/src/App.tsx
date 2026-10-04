import { useEffect, useState } from "react";
import { fetchMetros, runQuery } from "./api";
import { ConversationHistory } from "./components/ConversationHistory";
import { MetroDetailPanel } from "./components/MetroDetailPanel";
import { QueryResults } from "./components/QueryResults";
import { SearchBar } from "./components/SearchBar";
import { UsMetroMap } from "./components/UsMetroMap";
import type { ConversationTurn, MarketQueryResponse, Metro } from "./types";

const MAX_HISTORY_TURNS = 5;

export default function App() {
  const [metros, setMetros] = useState<Metro[]>([]);
  const [metrosLoading, setMetrosLoading] = useState(true);
  const [queryResponse, setQueryResponse] = useState<MarketQueryResponse | null>(null);
  const [lastQuery, setLastQuery] = useState("");
  const [history, setHistory] = useState<ConversationTurn[]>([]);
  const [queryId, setQueryId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetro, setSelectedMetro] = useState<Metro | null>(null);

  useEffect(() => {
    fetchMetros()
      .then(setMetros)
      .catch((err: Error) => setError(err.message))
      .finally(() => setMetrosLoading(false));
  }, []);

  async function handleSearch(query: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await runQuery(query, history);
      setQueryResponse(response);
      setLastQuery(query);
      setQueryId((id) => id + 1);
      setHistory((prev) => [...prev, { query, filters: response.filters }].slice(-MAX_HISTORY_TURNS));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setQueryResponse(null);
    setError(null);
    setHistory([]);
  }

  return (
    <div className="app">
      <header>
        <button className="home-link" onClick={handleReset} aria-label="Back to browse">
          <h1>Athena</h1>
        </button>
        <p className="tagline">Real estate market trends, searchable in plain English.</p>
        <p className="intro">
          Athena tracks US housing markets across 50 metros using real public data: Redfin and Apartment
          List for sale and rent listings, Census for household income and gross rent, Freddie Mac for
          mortgage rates, BLS for unemployment, and FHFA's house price index through FRED. Ask a question
          in plain English and a language model turns it into a structured query against that data. It
          never invents a number, and it tells you when a metro or metric has no data.
        </p>
      </header>

      <section className="app-section">
        <h2 className="section-label">01 · Ask</h2>
        <SearchBar onSearch={handleSearch} loading={loading} />
      </section>

      {error && <p className="error-banner">{error}</p>}

      {queryResponse ? (
        <>
          <button className="back-link" onClick={handleReset}>
            ← Back to browse
          </button>
          <ConversationHistory history={history.slice(0, -1)} />
          <QueryResults key={queryId} response={queryResponse} query={lastQuery} />
        </>
      ) : (
        <section className="app-section">
          <h2 className="section-label">02 · Browse</h2>
          <p className="explanation">Browse all 50 tracked metros, or search above.</p>
          {metrosLoading ? (
            <p className="empty-state">Loading metros…</p>
          ) : (
            <UsMetroMap metros={metros} onSelect={setSelectedMetro} />
          )}
        </section>
      )}

      {selectedMetro && (
        <MetroDetailPanel metro={selectedMetro} onClose={() => setSelectedMetro(null)} />
      )}

      <footer className="footnote">
        A few metros don't show rent or income badges — Apartment List and Census don't publish those
        metrics below the full-metro level there, so we never fake a number to fill the gap.
      </footer>
    </div>
  );
}
