import { useEffect, useState } from "react";
import { fetchMetros, runQuery } from "./api";
import { MetroDetailPanel } from "./components/MetroDetailPanel";
import { MetroGrid } from "./components/MetroGrid";
import { QueryResults } from "./components/QueryResults";
import { SearchBar } from "./components/SearchBar";
import type { MarketQueryResponse, Metro } from "./types";

export default function App() {
  const [metros, setMetros] = useState<Metro[]>([]);
  const [queryResponse, setQueryResponse] = useState<MarketQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetro, setSelectedMetro] = useState<Metro | null>(null);

  useEffect(() => {
    fetchMetros()
      .then(setMetros)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function handleSearch(query: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await runQuery(query);
      setQueryResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Athena</h1>
        <p className="tagline">Real estate market trends, searchable in plain English.</p>
      </header>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && <p className="error-banner">{error}</p>}

      {queryResponse ? (
        <QueryResults response={queryResponse} />
      ) : (
        <>
          <p className="explanation">Browse all 50 tracked metros, or search above.</p>
          <MetroGrid metros={metros} onSelect={setSelectedMetro} />
        </>
      )}

      {selectedMetro && (
        <MetroDetailPanel metro={selectedMetro} onClose={() => setSelectedMetro(null)} />
      )}
    </div>
  );
}
