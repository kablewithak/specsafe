import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { UnderstandSystemSection } from "./understand-system-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("UnderstandSystemSection", () => {
  it("teaches the governed experiment without changing the evidence contract", async () => {
    const user = userEvent.setup();

    render(<UnderstandSystemSection evidence={evidence} />);

    expect(
      screen.getByRole("heading", {
        name: "Can adaptive verification spend compute more intelligently?",
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", {
        name: "Compare three policies on the same six governed cases.",
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Sometimes useful. Not safe to activate." }),
    ).toBeVisible();

    for (const policy of evidence.policies) {
      expect(screen.getByText(policy.display_name)).toBeVisible();
    }

    expect(screen.getByText("Current confidence")).toBeVisible();
    expect(screen.getByText("Future correctness")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Causal information" }));
    expect(
      screen.getByText("Information that genuinely exists when the decision must be made."),
    ).toBeVisible();
  });
});
