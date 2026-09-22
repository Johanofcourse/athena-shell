import { FormEvent, useState } from "react";

const EXAMPLE_QUERIES = [
  "Condos in Austin under $400k that dropped in price",
  "Listings on the market over 60 days",
  "Homes relisted more than once in Denver",
  "3+ bedroom single family homes with a 5%+ price drop",
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
          placeholder="Ask about listing history, e.g. “price drops over 10% in the last month”"
          aria-label="Natural language listing search"
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
