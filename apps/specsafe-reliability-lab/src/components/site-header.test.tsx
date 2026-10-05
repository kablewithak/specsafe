import { render, screen, within } from "@testing-library/react";

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("keeps the blocked decision visible and provides responsive chapter navigation", () => {
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: /SpecSafe/i })).toHaveAttribute("href", "#overview");
    expect(screen.getByText("Activation blocked")).toBeVisible();

    const navigation = screen.getByRole("navigation", { name: "Primary navigation" });
    const navigationQueries = within(navigation);

    expect(navigationQueries.getByRole("link", { name: /Problem/i })).toHaveAttribute(
      "href",
      "#why-it-matters",
    );
    expect(navigationQueries.getByRole("link", { name: /Question/i })).toHaveAttribute(
      "href",
      "#north-star",
    );
    expect(navigationQueries.getByRole("link", { name: /Results/i })).toHaveAttribute(
      "href",
      "#policy-results",
    );
    expect(navigationQueries.getByRole("link", { name: /Safety gate/i })).toHaveAttribute(
      "href",
      "#confidence-gate",
    );
    expect(navigationQueries.getByRole("link", { name: /Meaning/i })).toHaveAttribute(
      "href",
      "#what-it-means",
    );
    expect(navigationQueries.getByRole("link", { name: /Evidence/i })).toHaveAttribute(
      "href",
      "#evidence",
    );
  });
});
