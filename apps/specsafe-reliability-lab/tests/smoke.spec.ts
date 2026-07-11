import { expect, test } from "@playwright/test";

const heroHeading = "When should AI spend more compute?";

for (const route of ["/"]) {
  test(`renders the governed visual story at ${route}`, async ({ page }) => {
    await page.goto(route);

    await expect(page.getByRole("heading", { name: heroHeading })).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Can adaptive verification spend compute more intelligently?",
      }),
    ).toBeVisible();
    await expect(page.getByText("Activation blocked").first()).toBeVisible();
    await expect(page.getByText("2 wins · 3 neutral · 1 loss")).toBeVisible();
    await expect(page.getByTestId("fixed-neutral-cases")).toContainText(
      "MPC5-101 · MPC5-102 · MPC5-106",
    );
    await expect(
      page.getByRole("heading", { name: "MPC5-103 · Moderate load" }),
    ).toBeVisible();
    await expect(page.getByText("KEEP_DIAGNOSTIC_ONLY", { exact: true }).first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow).toBe(false);
  });
}

test("supports keyboard navigation to the evidence explorer", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: heroHeading })).toBeVisible();

  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeAttached();
  await page.keyboard.press("Tab");
  await expect(skipLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main-content$/);
  await expect(page.locator("#main-content")).toBeVisible();

  await page.locator("#evidence").scrollIntoViewIfNeeded();
  const claimsTab = page.getByRole("tab", { name: "Claims" });
  await claimsTab.focus();
  await expect(claimsTab).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("No global policy winner is established.")).toBeVisible();
});
