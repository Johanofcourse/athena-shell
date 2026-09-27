import type { MarketQueryResponse } from "../types";
import { RankingChart } from "./RankingChart";
import { TrendChart } from "./TrendChart";

interface Props {
  response: MarketQueryResponse;
}

export function QueryResults({ response }: Props) {
  const { filters, explanation, results } = response;

  return (
    <div className="query-results">
      <p className="explanation">{explanation}</p>
      {results.length === 0 ? (
        <p className="empty-state">No data to show for this query.</p>
      ) : filters.sort_by === "value" ? (
        <RankingChart points={results} />
      ) : (
        <TrendChart points={results} />
      )}
    </div>
  );
}
