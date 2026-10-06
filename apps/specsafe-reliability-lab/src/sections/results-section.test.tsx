import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { ResultsSection } from "./results-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("ResultsSection", () => {
  it("defaults to fixed length and preserves neutral, loss, and win evidence", () => {
    render(<ResultsSection evidence={evidence} />);

    expect(screen.getByText("2 wins · 3 neutral · 1 loss")).toBeVisible();
    expect(screen.getByTestId("fixed-neutral-cases")).toHaveTextContent(
      "MPC5-101 · MPC5-102 · MPC5-106",
    );
    expect(
      screen.getByRole("heading", { name: "MPC5-103 · Moderate load" }),
    ).toBeVisible();
    expect(screen.getByText("+13.0")).toBeVisible();
    expect(screen.getByText("-1.0")).toBeVisible();
  });

  it("recomputes the view from evidence when static threshold is selected", async () => {
    const user = userEvent.setup();

    render(<ResultsSection evidence={evidence} />);

    await user.click(screen.getByRole("button", { name: "Static threshold" }));

    expect(screen.getByText("3 wins · 2 neutral · 1 loss")).toBeVisible();
    expect(screen.getByTestId("threshold-neutral-cases")).toHaveTextContent(
      "MPC5-101 · MPC5-102",
    );
    expect(screen.getByText("+1.6")).toBeVisible();
    expect(screen.getByRole("button", { name: "Static threshold" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("keeps exact values available through progressive disclosure", async () => {
    const user = userEvent.setup();

    render(<ResultsSection evidence={evidence} />);

    await user.click(screen.getByText("View exact values"));

    expect(
      screen.getByRole("table", {
        name: /Fixed length, static threshold, and adaptive utility across all six governed cases/i,
      }),
    ).toBeVisible();
  });
});
