import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import evidenceJson from "../../public/evidence/evidence_index.json";
import { evidenceIndexSchema } from "@/lib/evidence";

import { EvidenceExplorerSection } from "./evidence-explorer-section";

const evidence = evidenceIndexSchema.parse(evidenceJson);

describe("EvidenceExplorerSection", () => {
  it("renders the governed evidence boundary from the frozen contract", () => {
    render(<EvidenceExplorerSection evidence={evidence} />);

    expect(
      screen.getByRole("heading", {
        name: "Verify the boundary, not just the headline.",
      }),
    ).toBeVisible();
    const validComparisonsLabel = screen.getByText("Valid causal comparisons");
    const validComparisonsRow = validComparisonsLabel.closest("div");

    expect(validComparisonsRow).not.toBeNull();
    expect(
      within(validComparisonsRow as HTMLElement).getByText(
        evidence.valid_causal_comparisons.toString(),
      ),
    ).toBeVisible();

    expect(screen.getByText(evidence.schema_version)).toBeVisible();
  });

  it("keeps claims and non-claims inspectable in the Claims tab", async () => {
    const user = userEvent.setup();

    render(<EvidenceExplorerSection evidence={evidence} />);
    await user.click(screen.getByRole("tab", { name: "Claims" }));

    const claimsPanel = screen.getByRole("tabpanel", { name: "Claims" });

    expect(
      claimsPanel.textContent,
    ).toContain("No global policy winner is established.");
    expect(
      claimsPanel.textContent,
    ).toContain("Ranking safety regressed beyond tolerance, so activation was blocked.");
  });

  it("shows full source hashes and publication identity", async () => {
    const user = userEvent.setup();

    render(<EvidenceExplorerSection evidence={evidence} />);

    await user.click(screen.getByRole("tab", { name: "Sources" }));
    expect(screen.getByText(evidence.source_artifacts[0].sha256)).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Dataset" }));
    expect(
      screen.getByText(evidence.dataset_publication.published_revision),
    ).toBeVisible();
    expect(
      screen.getByText(evidence.dataset_publication.publication_manifest_sha256),
    ).toBeVisible();
  });
});
