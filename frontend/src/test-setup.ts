import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";

// React Testing Library's automatic afterEach cleanup only registers
// itself when the test runner exposes `afterEach` as a global - this
// project imports test functions explicitly instead of enabling Vitest's
// globals mode, so it never fired without this, leaving DOM from one
// test bleeding into the next within the same file.
afterEach(() => {
  cleanup();
});
