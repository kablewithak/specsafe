import { expect, test } from "@playwright/test";

test("keeps the primary navigation frozen while scrolling", async ({ page }) => {
  await page.goto("/");

  const header = page.locator("header");
  await expect(header).toBeVisible();

  const position = await header.evaluate((element) =>
    window.getComputedStyle(element).position,
  );
  expect(position).toBe("sticky");

  const initialTop = await header.evaluate((element) =>
    element.getBoundingClientRect().top,
  );

  await page.locator("#confidence-gate").scrollIntoViewIfNeeded();

  const scrolledTop = await header.evaluate((element) =>
    element.getBoundingClientRect().top,
  );

  expect(Math.abs(initialTop)).toBeLessThan(2);
  expect(Math.abs(scrolledTop)).toBeLessThan(2);
});

test("keeps anchor targets below the frozen navigation", async ({ page }) => {
  await page.goto("/");

  const evidenceLink = page
    .getByRole("navigation", { name: "Primary navigation" })
    .getByRole("link", { name: /Evidence/i });

  await evidenceLink.click();
  await expect(page).toHaveURL(/#evidence$/);

  const geometry = await page.evaluate(() => {
    const headerElement = document.querySelector("header");
    const target = document.querySelector("#evidence");

    if (!headerElement || !target) {
      throw new Error("Expected header and #evidence target.");
    }

    return {
      headerBottom: headerElement.getBoundingClientRect().bottom,
      targetTop: target.getBoundingClientRect().top,
    };
  });

  expect(geometry.targetTop).toBeGreaterThanOrEqual(geometry.headerBottom - 2);
});
