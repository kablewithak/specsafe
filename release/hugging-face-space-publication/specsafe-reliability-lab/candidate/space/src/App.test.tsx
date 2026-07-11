import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";
import evidenceJson from "../public/evidence/evidence_index.json";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(evidenceJson),
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SpecSafe visual shell", () => {
  it("frames the north star before presenting the mixed result", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "When should AI spend more compute?" }),
    ).toBeVisible();
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
  });

  it("makes wins, neutral cases, the loss, and blocked activation explicit", async () => {
    render(<App />);

    await screen.findByRole("heading", { name: "When should AI spend more compute?" });

    expect(screen.getAllByText("Activation blocked").length).toBeGreaterThan(0);
    expect(screen.getByText("2 wins · 3 neutral · 1 loss")).toBeVisible();
    expect(screen.getByText("3 wins · 2 neutral · 1 loss")).toBeVisible();
    expect(screen.getByTestId("fixed-neutral-cases")).toHaveTextContent(
      "MPC5-101 · MPC5-102 · MPC5-106",
    );
    expect(screen.getAllByText("KEEP_DIAGNOSTIC_ONLY").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ranking_safety_regression").length).toBeGreaterThan(0);
  });

  it("renders all six governed cases and preserves the important identities", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: "When should AI spend more compute?" });

    for (const caseId of ["MPC5-101", "MPC5-102", "MPC5-103", "MPC5-104", "MPC5-105", "MPC5-106"]) {
      expect(screen.getAllByText(caseId).length).toBeGreaterThan(0);
    }
    expect(
      screen.getAllByText("The adaptive policy was too conservative under moderate load.").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("The adaptive policy avoided large losses under saturated load.").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("The adaptive policy avoided losses under jagged capacity.").length,
    ).toBeGreaterThan(0);
  });

  it("keeps the non-claims visible in the evidence explorer", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: "When should AI spend more compute?" });

    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Claims" }));

    expect(await screen.findByText("No global policy winner is established.")).toBeVisible();
    expect(
      screen.getByText("No production throughput, latency, cost, or serving result is established."),
    ).toBeVisible();
  });
});
