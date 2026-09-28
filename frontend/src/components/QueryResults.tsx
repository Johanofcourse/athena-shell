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
  const { filters, explanation, results } = response;

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
