import { render, screen, within } from "@testing-library/react";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";
import { PolicyCaseMatrix } from "./policy-case-matrix";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("PolicyCaseMatrix", () => {
  it("renders all six cases, exact policy values, and explicit neutral outcomes", () => {
    render(<PolicyCaseMatrix cases={evidence.cases} />);

    const table = screen.getByRole("table", {
      name: /Fixed length, static threshold, and adaptive utility across all six governed cases/i,
    });

    for (const caseId of evidence.cases.map((item) => item.case_id)) {
      expect(within(table).getByText(caseId)).toBeVisible();
    }

    expect(within(table).getAllByText("Neutral")).toHaveLength(3);
    expect(within(table).getAllByText("Adaptive higher")).toHaveLength(2);
    expect(within(table).getByText("Adaptive lower")).toBeVisible();

    const lossRow = within(table).getByText("MPC5-103").closest("tr");
    expect(lossRow).not.toBeNull();
    expect(within(lossRow as HTMLElement).getAllByText("1.0")).toHaveLength(2);
    expect(within(lossRow as HTMLElement).getByText("0.0")).toBeVisible();
  });
});
