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
    // The backend already prefers one chunk per distinct section, but if
    // a metro's report only has a couple of sections at all, two chunks
    // from the same one can still happen - label the repeat instead of
    // showing two identical-looking headings with no way to tell them
    // apart.
    const sectionCounts: Record<string, number> = {};
    return (
      <div className="query-results">
        <p className="explanation">{explanation}</p>
        <div className="commentary">
          {commentary.chunks.map((chunk, i) => {
            sectionCounts[chunk.section] = (sectionCounts[chunk.section] ?? 0) + 1;
            const label =
              sectionCounts[chunk.section] > 1 ? `${chunk.section} (continued)` : chunk.section;
            return (
              <div className="commentary-chunk" key={i}>
                <h3 className="commentary-section">{label}</h3>
                {/* Collapse the PDF's own line-wrap breaks into flowing
                    prose - preserving them (the raw extracted text has a
                    newline after every visual line, not every paragraph)
                    made this read as a wall of disconnected short lines
                    rather than real paragraphs. */}
                <p className="commentary-text">{chunk.text.replace(/\s*\n+\s*/g, " ").trim()}</p>
              </div>
            );
          })}
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
