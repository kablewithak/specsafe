import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DefinitionExplorer } from "./definition-explorer";

describe("DefinitionExplorer", () => {
  it("reveals one relevant definition at a time without hiding the concept labels", async () => {
    const user = userEvent.setup();

    render(<DefinitionExplorer />);

    expect(
      screen.getByText(
        "Extra checking work used to decide whether an AI system should trust or continue with a candidate output.",
      ),
    ).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Capacity" }));

    expect(
      screen.getByText(
        "How much verification compute is available when the policy must make its decision.",
      ),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Capacity" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
