import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { MarketQueryFilters, MarketQueryResponse } from "../types";
import { QueryResults } from "./QueryResults";

// Only the empty-results branch is covered here - the chart-rendering
// branch (RankingChart/TrendChart, via Recharts) is verified in a real
// browser (see the Playwright checks run alongside each UI change),
// not jsdom, which doesn't implement the layout/ResizeObserver behavior
// Recharts needs to size itself correctly.

function baseFilters(overrides: Partial<MarketQueryFilters>): MarketQueryFilters {
  return {
    metros: ["Anaheim, CA"],
    metric: "median_rent",
    bed_size: null,
    start_period: null,
    end_period: null,
    sort_by: "period",
    sort_order: "desc",
    limit: 60,
    unsupported_aspects: [],
    ...overrides,
  };
}

function response(overrides: Partial<MarketQueryResponse>): MarketQueryResponse {
  return {
    filters: baseFilters({}),
    explanation: "Showing median rent for Anaheim, CA.",
    unmatched_metros: [],
    no_data_metros: [],
    approximated_metros: [],
    results: [],
    ...overrides,
  };
}

describe("QueryResults", () => {
  it("shows the explanation text and an empty-state message when there are no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(screen.getByText("Showing median rent for Anaheim, CA.")).toBeInTheDocument();
    expect(screen.getByText("No data to show for this query.")).toBeInTheDocument();
  });

  it("does not render an analysis summary when there are no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(document.querySelector(".analysis")).not.toBeInTheDocument();
  });

  it("still renders the feedback widget and interpretation panel with no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(screen.getByText("Was this interpreted correctly?")).toBeInTheDocument();
    expect(screen.getByText("How this was interpreted")).toBeInTheDocument();
  });
});
