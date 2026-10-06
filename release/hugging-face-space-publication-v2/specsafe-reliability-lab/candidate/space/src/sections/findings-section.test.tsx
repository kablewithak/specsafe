import { render, screen } from "@testing-library/react";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { FindingsSection } from "./findings-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("FindingsSection", () => {
  it("keeps supported claims and non-claims visibly separate", () => {
    render(<FindingsSection evidence={evidence} />);

    expect(
      screen.getByRole("heading", {
        name: "Reliability is the gate, not the average score.",
      }),
    ).toBeVisible();

    expect(screen.getByText("Supported by the evidence")).toBeVisible();
    expect(screen.getByText("Not established")).toBeVisible();

    for (const claim of evidence.supported_claims) {
      expect(screen.getByText(claim)).toBeVisible();
    }

    for (const claim of evidence.non_claims) {
      expect(screen.getByText(claim)).toBeVisible();
    }
  });

  it("preserves the central negative-evidence interpretation", () => {
    render(<FindingsSection evidence={evidence} />);

    expect(
      screen.getByText(
        "Adaptive verification can help without being a global winner.",
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        "A better average metric does not authorize automation.",
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Blocking promotion is a successful reliability outcome.",
      ),
    ).toBeVisible();
  });
});
