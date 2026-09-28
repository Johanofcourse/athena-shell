import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Metro } from "../types";
import { MetroGrid } from "./MetroGrid";

function metro(overrides: Partial<Metro>): Metro {
  return {
    id: "testville-ts",
    canonical_name: "Testville, TS",
    state: "TS",
    has_sale_data: true,
    has_rent_data: true,
    has_income_data: true,
    census_gross_rent_county: null,
    ...overrides,
  };
}

describe("MetroGrid", () => {
  it("shows all three badges for a fully-covered metro", () => {
    render(<MetroGrid metros={[metro({})]} onSelect={() => {}} />);
    const card = screen.getByRole("button", { name: /Testville, TS/ });
    expect(within(card).getByText("Sale data")).toBeInTheDocument();
    expect(within(card).getByText("Rent data")).toBeInTheDocument();
    expect(within(card).getByText("Income data")).toBeInTheDocument();
  });

  it("hides rent and income badges for a metro-division gap metro", () => {
    render(
      <MetroGrid
        metros={[
          metro({
            id: "anaheim-ca",
            canonical_name: "Anaheim, CA",
            has_rent_data: false,
            has_income_data: false,
          }),
        ]}
        onSelect={() => {}}
      />,
    );
    const card = screen.getByRole("button", { name: /Anaheim, CA/ });
    expect(within(card).getByText("Sale data")).toBeInTheDocument();
    expect(within(card).queryByText("Rent data")).not.toBeInTheDocument();
    expect(within(card).queryByText("Income data")).not.toBeInTheDocument();
  });

  it("calls onSelect with the clicked metro", () => {
    const onSelect = vi.fn();
    const testville = metro({});
    render(<MetroGrid metros={[testville]} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button", { name: /Testville, TS/ }));
    expect(onSelect).toHaveBeenCalledWith(testville);
  });

  it("renders one card per metro", () => {
    render(
      <MetroGrid
        metros={[metro({ id: "a", canonical_name: "A, TS" }), metro({ id: "b", canonical_name: "B, TS" })]}
        onSelect={() => {}}
      />,
    );
    expect(screen.getAllByRole("button")).toHaveLength(2);
  });
});
