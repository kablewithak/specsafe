import { render, screen } from "@testing-library/react";

import evidenceJson from "../../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { UtilityDifferencePlot } from "./utility-difference-plot";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("UtilityDifferencePlot", () => {
  it("derives adaptive-minus-fixed differences from frozen evidence", () => {
    render(<UtilityDifferencePlot cases={evidence.cases} baseline="fixed" />);

    expect(
      screen.getByRole("img", {
        name: /Adaptive utility difference compared with fixed length/i,
      }),
    ).toBeVisible();

    expect(screen.getAllByText("0.0")).toHaveLength(3);
    expect(screen.getByText("-1.0")).toBeVisible();
    expect(screen.getByText("+13.0")).toBeVisible();
    expect(screen.getByText("+7.8")).toBeVisible();
  });

  it("changes only the comparator-derived differences when threshold is selected", () => {
    render(<UtilityDifferencePlot cases={evidence.cases} baseline="threshold" />);

    expect(screen.getAllByText("0.0")).toHaveLength(2);
    expect(screen.getByText("+1.6")).toBeVisible();
  });
});
