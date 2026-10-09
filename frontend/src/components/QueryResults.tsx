import { summarizeResults } from "../analysis";
import type { MarketQueryResponse } from "../types";
import { FeedbackWidget } from "./FeedbackWidget";
import { InterpretationPanel } from "./InterpretationPanel";
import { RankingChart } from "./RankingChart";
import { TrendChart } from "./TrendChart";

interface Props {
  response: MarketQueryResponse;
  query: string;
}

export function QueryResults({ response, query }: Props) {
  const { filters, explanation, results, commentary } = response;

  if (commentary) {
    return (
      <div className="query-results">
        <p className="explanation">{explanation}</p>
        <div className="commentary">
          {commentary.chunks.map((chunk, i) => (
            <div className="commentary-chunk" key={i}>
              <h3 className="commentary-section">{chunk.section}</h3>
              <p className="commentary-text">{chunk.text}</p>
            </div>
          ))}
          <p className="commentary-citation">
            Source: HUD Comprehensive Housing Market Analysis, {commentary.metro} — as of{" "}
            {commentary.as_of_date} ({commentary.source_file})
          </p>
        </div>
      </div>
    );
  }

  // filters is only ever null alongside a populated commentary, so this
  // shouldn't happen in practice - kept so a future response shape change
  // degrades to an empty state instead of a crash.
  if (!filters) {
    return (
      <div className="query-results">
        <p className="explanation">{explanation}</p>
      </div>
    );
  }

  return (
    <div className="query-results">
      <p className="explanation">{explanation}</p>
      {results.length === 0 ? (
        <p className="empty-state">No data to show for this query.</p>
      ) : (
        <>
          {filters.sort_by === "value" ? (
            <RankingChart points={results} metric={filters.metric} />
          ) : (
            <TrendChart points={results} metric={filters.metric} />
          )}
          <p className="analysis">{summarizeResults(results, filters.metric, filters.sort_by)}</p>
        </>
      )}
      <FeedbackWidget query={query} filters={filters} />
      <InterpretationPanel filters={filters} />
    </div>
  );
}
