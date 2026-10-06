import { render, screen } from "@testing-library/react";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { HeroSection } from "./hero-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("HeroSection", () => {
  it("states the blocked-promotion reason in plain language before machine state", () => {
    render(<HeroSection evidence={evidence} />);

    expect(
      screen.getByRole("heading", {
        name: "When should AI spend more compute?",
      }),
    ).toBeVisible();

    expect(
      screen.getByRole("heading", {
        name: "Calibration improved, but confidence ranking got worse.",
      }),
    ).toBeVisible();

    expect(screen.getByText("Diagnostic only")).toBeVisible();
    expect(screen.getByText("Ranking safety regressed")).toBeVisible();
    expect(
      screen.getByText("24.36× beyond allowed degradation"),
    ).toBeVisible();

    expect(screen.getByText("KEEP_DIAGNOSTIC_ONLY")).toBeVisible();
  });
});
