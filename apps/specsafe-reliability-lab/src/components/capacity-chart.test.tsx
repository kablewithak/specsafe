import { render, screen } from "@testing-library/react";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { CapacityChart } from "./capacity-chart";
import { evidenceIndexSchema } from "@/lib/evidence";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("CapacityChart", () => {
  it("renders the exact six governed cases and all three policy series", () => {
    const { container } = render(<CapacityChart cases={evidence.cases} />);

    expect(
      screen.getByRole("img", {
        name: /Utility comparison across six governed capacity cases/,
      }),
    ).toBeVisible();
    for (const caseId of evidence.cases.map((item) => item.case_id)) {
      expect(screen.getByText(caseId)).toBeVisible();
    }
    expect(container.querySelectorAll("rect")).toHaveLength(18);
    expect(screen.getByText("Fixed length")).toBeVisible();
    expect(screen.getByText("Static threshold")).toBeVisible();
    expect(screen.getByText("Adaptive")).toBeVisible();
  });
});
