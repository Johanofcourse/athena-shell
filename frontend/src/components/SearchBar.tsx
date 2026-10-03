import { FormEvent, useState } from "react";

const EXAMPLE_QUERIES = [
  "How has rent changed in Austin over the last two years?",
  "Which metros have the lowest unemployment right now?",
  "How have 30-year mortgage rates changed since 2022?",
  "How has the house price index changed in Denver?",
];

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (value.trim()) onSearch(value.trim());
  }

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about market trends, e.g. “how has rent changed in Denver”"
          aria-label="Natural language market trend search"
        />
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="examples">
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example}
            type="button"
            className="example-chip"
            onClick={() => {
              setValue(example);
              onSearch(example);
            }}
            disabled={loading}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
