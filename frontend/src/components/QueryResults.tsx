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

// The backend marks a real in-page subheading (e.g. "Rental Construction
// Activity Trends" appearing mid-page, not just the page's own running
// header) with a leading "## ", separated from surrounding paragraphs by
// a blank line - see _looks_like_a_heading in ingest_market_data.py.
// Splitting on that here is what gives a commentary chunk real visual
// structure instead of one run-on paragraph.
function renderCommentaryBlocks(text: string) {
  return text.split("\n\n").map((block, i) =>
    block.startsWith("## ") ? (
      <h4 className="commentary-subheading" key={i}>
        {block.slice(3)}
      </h4>
    ) : (
      <p className="commentary-text" key={i}>
        {block}
      </p>
    ),
  );
}

export function QueryResults({ response, query }: Props) {
  const { filters, explanation, results, commentary, narrative, source_citation: sourceCitation } = response;

  if (commentary) {
    // The backend already prefers one chunk per distinct section, but if
    // a metro's report only has a couple of sections at all, two chunks
    // from the same one can still happen - label the repeat instead of
    // showing two identical-looking headings with no way to tell them
    // apart.
    const sectionCounts: Record<string, number> = {};
    return (
      <div className="query-results">
        {/* The actual answer - a thesis-first paraphrase of the chunks
            below (see market_commentary.synthesize_commentary_answer) -
            gets its own prominent treatment, not the same small, muted
            caption style .explanation uses for a chart's one-line filter
            summary. This is the part someone reads first; the chunks
            below are the citations for anyone checking it. */}
        <p className="commentary-summary">{explanation}</p>
        <div className="commentary">
          <p className="commentary-sources-label">Source excerpts</p>
          {commentary.chunks.map((chunk, i) => {
            sectionCounts[chunk.section] = (sectionCounts[chunk.section] ?? 0) + 1;
            const label =
              sectionCounts[chunk.section] > 1 ? `${chunk.section} (continued)` : chunk.section;
            return (
              <div className="commentary-chunk" key={i}>
                <h3 className="commentary-section">
                  <span className="commentary-index">{i + 1}</span> {label}
                  <span className="commentary-page"> · p. {chunk.page_number}</span>
                </h3>
                {renderCommentaryBlocks(chunk.text)}
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

  // Inverted pyramid, the same shape a news article uses (Johan: "most
  // important info on top... important details, then general info and
  // background/citations, and graphs numbers at the bottom"): the thesis
  // leads, filter/caveat detail and the source citation follow as
  // supporting context, and the chart - the raw evidence, for whoever
  // wants to verify the thesis rather than just read it - comes last.
  // Presenting it in that order is also the whole point of asking for a
  // narrative at all: people read the facts and draw their own
  // conclusions, the same as an article, rather than a graph being the
  // first and only thing they see.
  return (
    <div className="query-results">
      {results.length === 0 ? (
        <>
          <p className="explanation">{explanation}</p>
          <p className="empty-state">No data to show for this query.</p>
        </>
      ) : (
        <>
          {/* Falls back to the deterministic analysis.ts sentence if the
              backend's LLM synthesis didn't run or failed - never shows
              nothing. Same prominent treatment as a commentary answer
              (.commentary-summary), reused rather than duplicated, so
              both response types read as "the answer first." */}
          <p className="commentary-summary">
            {narrative ?? summarizeResults(results, filters.metric, filters.sort_by)}
          </p>
          <p className="explanation">{explanation}</p>
          {sourceCitation && <p className="commentary-citation">Source: {sourceCitation}</p>}
          {filters.sort_by === "value" ? (
            <RankingChart points={results} metric={filters.metric} />
          ) : (
            <TrendChart points={results} metric={filters.metric} />
          )}
        </>
      )}
      <FeedbackWidget query={query} filters={filters} />
      <InterpretationPanel filters={filters} />
    </div>
  );
}
