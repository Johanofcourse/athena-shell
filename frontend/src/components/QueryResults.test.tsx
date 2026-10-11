import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { MarketCommentaryResult, MarketQueryFilters, MarketQueryResponse } from "../types";
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
    commentary: null,
    narrative: null,
    source_citation: null,
    ...overrides,
  };
}

function baseCommentary(overrides: Partial<MarketCommentaryResult>): MarketCommentaryResult {
  return {
    metro: "Austin, TX",
    as_of_date: "July 1, 2024",
    source_file: "AustinRoundRockTX-CHMA-24.pdf",
    chunks: [{ section: "Rental Market", page_number: 30, text: "Rents declined as new supply outpaced demand." }],
    ...overrides,
  };
}

describe("QueryResults", () => {
  it("shows the explanation text and an empty-state message when there are no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(screen.getByText("Showing median rent for Anaheim, CA.")).toBeInTheDocument();
    expect(screen.getByText("No data to show for this query.")).toBeInTheDocument();
  });

  it("does not render a summary paragraph when there are no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(document.querySelector(".commentary-summary")).not.toBeInTheDocument();
  });

  it("shows the backend narrative, prominently, above the chart when present", () => {
    render(
      <QueryResults
        response={response({
          results: [{ metro: "Anaheim, CA", period: "2024-01-01", value: 2000 }],
          narrative: "Rent in Anaheim has climbed steadily this year.",
        })}
        query="What's the rent trend in Anaheim?"
      />,
    );
    expect(screen.getByText("Rent in Anaheim has climbed steadily this year.")).toBeInTheDocument();
  });

  it("falls back to the deterministic analysis summary when narrative is null", () => {
    render(
      <QueryResults
        response={response({
          results: [{ metro: "Anaheim, CA", period: "2024-01-01", value: 2000 }],
          narrative: null,
        })}
        query="What's the rent trend in Anaheim?"
      />,
    );
    expect(screen.getByText("Anaheim, CA: $2,000.")).toBeInTheDocument();
  });

  it("shows the source citation when present, and omits the line when it's not", () => {
    const { rerender } = render(
      <QueryResults
        response={response({
          results: [{ metro: "Anaheim, CA", period: "2024-01-01", value: 2000 }],
          source_citation: "Apartment List",
        })}
        query="What's the rent trend in Anaheim?"
      />,
    );
    expect(screen.getByText("Source: Apartment List")).toBeInTheDocument();

    rerender(
      <QueryResults
        response={response({
          results: [{ metro: "Anaheim, CA", period: "2024-01-01", value: 2000 }],
          source_citation: null,
        })}
        query="What's the rent trend in Anaheim?"
      />,
    );
    expect(screen.queryByText(/^Source:/)).not.toBeInTheDocument();
  });

  it("orders the thesis before supporting detail before the chart - inverted pyramid, not a caption-then-graph layout", () => {
    render(
      <QueryResults
        response={response({
          results: [{ metro: "Anaheim, CA", period: "2024-01-01", value: 2000 }],
          narrative: "Rent in Anaheim has climbed steadily this year.",
          source_citation: "Apartment List",
        })}
        query="What's the rent trend in Anaheim?"
      />,
    );
    const container = document.querySelector(".query-results")!;
    const html = container.innerHTML;
    const narrativeIndex = html.indexOf("Rent in Anaheim has climbed steadily this year.");
    const explanationIndex = html.indexOf("Showing median rent for Anaheim, CA.");
    const citationIndex = html.indexOf("Source: Apartment List");
    const chartIndex = html.indexOf("chart-card");
    expect(narrativeIndex).toBeLessThan(explanationIndex);
    expect(explanationIndex).toBeLessThan(citationIndex);
    expect(citationIndex).toBeLessThan(chartIndex);
  });

  it("still renders the feedback widget and interpretation panel with no results", () => {
    render(<QueryResults response={response({})} query="What's the rent trend in Anaheim?" />);
    expect(screen.getByText("Was this interpreted correctly?")).toBeInTheDocument();
    expect(screen.getByText("How this was interpreted")).toBeInTheDocument();
  });

  it("renders a commentary response's chunks and citation instead of a chart", () => {
    render(
      <QueryResults
        response={response({
          filters: null,
          explanation: "Showing HUD market commentary for Austin, TX, as of July 1, 2024.",
          commentary: baseCommentary({}),
        })}
        query="Why is rent falling in Austin?"
      />,
    );
    expect(screen.getByText("Rental Market")).toBeInTheDocument();
    expect(screen.getByText("Rents declined as new supply outpaced demand.")).toBeInTheDocument();
    expect(screen.getByText(/AustinRoundRockTX-CHMA-24\.pdf/)).toBeInTheDocument();
  });

  it("does not render the chart, feedback widget, or interpretation panel for a commentary response", () => {
    render(
      <QueryResults
        response={response({ filters: null, commentary: baseCommentary({}) })}
        query="Why is rent falling in Austin?"
      />,
    );
    expect(screen.queryByText("Was this interpreted correctly?")).not.toBeInTheDocument();
    expect(screen.queryByText("How this was interpreted")).not.toBeInTheDocument();
    expect(screen.queryByText("No data to show for this query.")).not.toBeInTheDocument();
  });

  it("labels a repeated section as (continued) instead of showing two identical headings", () => {
    render(
      <QueryResults
        response={response({
          filters: null,
          commentary: baseCommentary({
            chunks: [
              { section: "Rental Market", page_number: 30, text: "First excerpt about rent." },
              { section: "Rental Market", page_number: 33, text: "Second excerpt about rent." },
            ],
          }),
        })}
        query="Why is rent falling in Austin?"
      />,
    );
    expect(screen.getByText("Rental Market")).toBeInTheDocument();
    expect(screen.getByText("Rental Market (continued)")).toBeInTheDocument();
  });

  it("renders a '## ' marked block as a subheading, separate from the surrounding paragraphs", () => {
    render(
      <QueryResults
        response={response({
          filters: null,
          commentary: baseCommentary({
            chunks: [
              {
                section: "Rental Market",
                page_number: 30,
                text: "Rents declined this quarter.\n\n## Apartment Market Conditions\n\nVacancy increased to 14 percent.",
              },
            ],
          }),
        })}
        query="Why is rent falling in Austin?"
      />,
    );
    const subheading = screen.getByText("Apartment Market Conditions");
    expect(subheading.tagName).toBe("H4");
    expect(screen.getByText("Rents declined this quarter.")).toBeInTheDocument();
    expect(screen.getByText("Vacancy increased to 14 percent.")).toBeInTheDocument();
  });

  it("falls back to just the explanation when both filters and commentary are null, instead of crashing", () => {
    render(<QueryResults response={response({ filters: null })} query="anything" />);
    expect(screen.getByText("Showing median rent for Anaheim, CA.")).toBeInTheDocument();
  });
});
