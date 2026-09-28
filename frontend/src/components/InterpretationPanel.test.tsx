import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { MarketQueryFilters } from "../types";
import { InterpretationPanel } from "./InterpretationPanel";

function baseFilters(overrides: Partial<MarketQueryFilters>): MarketQueryFilters {
  return {
    metros: [],
    metric: "median_sale_price",
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

function rowValue(label: string): string {
  const dt = screen.getByText(label);
  const row = dt.closest(".interpretation-row") as HTMLElement;
  return within(row).getByRole("definition").textContent ?? "";
}

describe("InterpretationPanel", () => {
  it("shows the exact resolved metric and metros, not a paraphrase", () => {
    render(<InterpretationPanel filters={baseFilters({ metros: ["Austin, TX"], metric: "median_rent" })} />);
    expect(rowValue("Metros")).toBe("Austin, TX");
    expect(rowValue("Metric")).toBe("median_rent");
  });

  it("renders a null/empty field as an em dash, not blank or 'null'", () => {
    render(<InterpretationPanel filters={baseFilters({ bed_size: null })} />);
    expect(rowValue("Bed size")).toBe("—");
  });

  it("renders an empty array as an em dash", () => {
    render(<InterpretationPanel filters={baseFilters({ unsupported_aspects: [] })} />);
    expect(rowValue("Flagged as unsupported")).toBe("—");
  });

  it("joins a non-empty array with commas", () => {
    render(<InterpretationPanel filters={baseFilters({ unsupported_aspects: ["school quality", "crime rate"] })} />);
    expect(rowValue("Flagged as unsupported")).toBe("school quality, crime rate");
  });

  it("is collapsed by default (a <details> element, not open)", () => {
    render(<InterpretationPanel filters={baseFilters({})} />);
    const details = document.querySelector("details.interpretation-panel") as HTMLDetailsElement;
    expect(details.open).toBe(false);
  });
});
