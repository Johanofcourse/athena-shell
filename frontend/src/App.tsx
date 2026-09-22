import { useEffect, useState } from "react";
import { fetchListing, fetchListings, runQuery } from "./api";
import { ListingDetailPanel } from "./components/ListingDetailPanel";
import { ResultsList } from "./components/ResultsList";
import { SearchBar } from "./components/SearchBar";
import type { Listing, ListingDetail } from "./types";

export default function App() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedListing, setSelectedListing] = useState<ListingDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchListings(50)
      .then(setListings)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function handleSearch(query: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await runQuery(query);
      setListings(response.results);
      setExplanation(response.explanation);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelect(id: string) {
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const detail = await fetchListing(id);
      setSelectedListing(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listing");
      setSelectedId(null);
    } finally {
      setDetailLoading(false);
    }
  }

  function handleClose() {
    setSelectedId(null);
    setSelectedListing(null);
  }

  return (
    <div className="app">
      <header>
        <h1>Athena</h1>
        <p className="tagline">Real estate listing history, searchable in plain English.</p>
      </header>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && <p className="error-banner">{error}</p>}
      {explanation && !error && <p className="explanation">{explanation}</p>}

      <ResultsList listings={listings} onSelect={handleSelect} />

      {selectedId && (
        <ListingDetailPanel
          listing={selectedListing}
          loading={detailLoading}
          onClose={handleClose}
        />
      )}
    </div>
  );
}
