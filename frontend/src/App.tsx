import { useEffect, useState } from "react";
import { fetchMetros, runQuery } from "./api";
import athenaIcon from "./assets/pallas-athena-icon.jpg";
import athenaPainting from "./assets/pallas-athena.jpg";
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
      // Only a query_market_metrics response has filters to replay as
      // conversation state - a commentary response's filters is null, and
      // isn't carried into history (see ConversationTurn/backend docs).
      const { filters } = response;
      if (filters) {
        setHistory((prev) => [...prev, { query, filters }].slice(-MAX_HISTORY_TURNS));
      }
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
        {/* True background decoration - absolutely positioned, out of
            document flow entirely, so it has zero influence on any
            box's height or position. Earlier versions kept finding new
            ways to let her affect layout (a flex row's height, a
            guessed min-height) and each one leaked a gap somewhere;
            this can't, because nothing here ever measures her. */}
        <img className="brand-watermark" src={athenaPainting} alt="" aria-hidden="true" />
        <div className="brand-text">
          <button className="home-link" onClick={handleReset} aria-label="Back to browse">
            <span className="home-link-row">
              <h1>Athena</h1>
              {/* The big background portrait is hidden below 560px (she
                  was overlapping the wrapped tagline there - see
                  .brand-watermark's mobile rule). This is a compact
                  stand-in just for that width: the same face crop
                  already validated at small sizes for the favicon, sized
                  to sit cleanly next to the wordmark instead of behind
                  running text. */}
              <img className="wordmark-icon" src={athenaIcon} alt="" aria-hidden="true" />
            </span>
          </button>
          <p className="tagline">Intelligent Real Estate Trends, searchable in plain English.</p>
          <details className="intro">
            <summary className="intro-label">What is this?</summary>
            <p className="intro-body">
              Athena tracks US housing markets across 50 metros using real public data: Redfin and
              Apartment List for sale and rent listings, Census for household income and gross rent,
              Freddie Mac for mortgage rates, BLS for unemployment, and FHFA's house price index through
              FRED. Ask a question in plain English and a language model turns it into a structured query
              against that data. It never invents a number, and it tells you when a metro or metric has
              no data.
            </p>
          </details>
        </div>
      </header>

      <section className="ask">
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
        <section className="browse">
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
        <p>
          A few metros don't show rent or income badges — Apartment List and Census don't publish those
          metrics below the full-metro level there, so we never fake a number to fill the gap.
        </p>
        <p>
          Portrait: "Pallas Athena," Rembrandt van Rijn, c. 1655 — public domain, Wikimedia Commons.
        </p>
      </footer>
    </div>
  );
}
