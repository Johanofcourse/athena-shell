import { FormEvent, useState } from "react";

const EXAMPLE_QUERY_POOL = [
  "How has rent changed in Austin over the last two years?",
  "Which metros have the lowest unemployment right now?",
  "How have 30-year mortgage rates changed since 2022?",
  "How has the house price index changed in Denver?",
  "Where is the median sale price highest right now?",
  "How has median household income changed in Atlanta?",
  "How have homes sold changed in Phoenix over the last year?",
  "How long do homes stay on the market in Seattle?",
  "Which metros have the highest rent-to-income ratio?",
  "How have 15-year mortgage rates changed since 2023?",
  // Showcasing the newer metrics - each phrasing verified end-to-end
  // against the real API before adding, same as every example above.
  "How does the commute compare between Austin and Denver?",
  "Which metros have the highest property taxes?",
  "How has the population changed in Austin over the last decade?",
  "Which metros have the highest natural disaster risk?",
  // "Why" questions only resolve for the 23 metros with real HUD CHMA
  // coverage (not all 50) - confirmed each of these specifically has
  // commentary, and that the real answer actually matches the question's
  // premise, before adding. A couple of other candidates tested here
  // (Houston construction, Miami rental competitiveness) correctly
  // contradicted their own premise instead of confirming it - a genuine,
  // on-brand demonstration of the grounding discipline, but not what a
  // first-time visitor's default example chip should lead with.
  "Why has rent been declining in Austin?",
  "Why are home prices rising in Dallas?",
  "Why is population growing in Tampa?",
];
const EXAMPLE_COUNT = 4;

function pickExamples(): string[] {
  const shuffled = [...EXAMPLE_QUERY_POOL];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled.slice(0, EXAMPLE_COUNT);
}

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");
  const [examples] = useState(pickExamples);

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
          placeholder="Make your query"
          aria-label="Natural language market trend search"
        />
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="examples">
        {examples.map((example) => (
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
