import { render, screen } from "@testing-library/react";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { ConfidenceGateSection } from "./confidence-gate-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("ConfidenceGateSection", () => {
  it("separates metric improvement from promotion authorization", () => {
    render(<ConfidenceGateSection evidence={evidence} />);

    expect(
      screen.getByRole("heading", {
        name: "Calibration improved. Ranking safety failed.",
      }),
    ).toBeVisible();

    expect(screen.getByText("Two probability metrics improved")).toBeVisible();
    expect(screen.getByText("Ranking safety regressed")).toBeVisible();
    expect(screen.getByText("KEEP_DIAGNOSTIC_ONLY")).toBeVisible();
    expect(screen.getByText("ranking_safety_regression")).toBeVisible();
  });

  it("preserves the exact gate-breaking evidence and labels the positive multiple correctly", () => {
    render(<ConfidenceGateSection evidence={evidence} />);

    expect(
      screen.getByText(
        evidence.calibration_gate.maximum_allowed_auroc_degradation.toString(),
      ),
    ).toBeVisible();
    expect(
      screen.getByText(evidence.calibration_gate.observed_auroc_delta.toString()),
    ).toBeVisible();
    expect(screen.getByText("24.36×")).toBeVisible();
    expect(screen.getByText("Degradation magnitude")).toBeVisible();
  });

  it("shows the independent holdout composition", () => {
    render(<ConfidenceGateSection evidence={evidence} />);

    expect(
      screen.getByText(
        "Holdout: 192 records · 136 positive · 56 negative · status: unfit_use_conservative_fallback",
      ),
    ).toBeVisible();
  });
});
