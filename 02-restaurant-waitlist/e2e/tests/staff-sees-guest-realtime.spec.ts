import { test, expect, type Page } from "@playwright/test";

/**
 * Two-session flow against the live docker-compose.yml stack:
 *
 *   1. Session 1 (staff): sign in and load the dashboard.
 *   2. Session 2 (guest): a fully separate browser session opens the
 *      public join link and joins the waitlist.
 *   3. Back in session 1, with no reload or manual action from us, watch
 *      the new guest appear on the dashboard.
 *
 * "Real-time" here means what the product actually does: the dashboard's
 * summary counts poll automatically every 20s (see the `refetchInterval`
 * on `dashboardQuery` in `frontend/src/routes/staff.index.tsx`), so step 3
 * waits on that poll rather than reloading the page. The entries list
 * itself has no such timer - only the summary does - so seeing the new
 * guest's row (not just the count) still needs the dashboard's own
 * "Refresh" button, exactly as a staff member would use it.
 */

const STAFF_USERNAME = "manager";
const STAFF_PASSWORD = "waitlist123";

async function loginAsStaff(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Username or email").fill(STAFF_USERNAME);
  await page.getByLabel("Password").fill(STAFF_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Tonight's waitlist" })).toBeVisible();
}

function pendingReviewValue(page: Page) {
  return page
    .locator('section[aria-label="Queue summary"] .surface-card', { hasText: "Pending review" })
    .locator("p")
    .nth(1);
}

test("staff dashboard picks up a new guest join without a page reload", async ({ browser }) => {
  // Session 1: staff member signed in, watching the dashboard.
  const staffContext = await browser.newContext();
  const staffPage = await staffContext.newPage();
  await loginAsStaff(staffPage);

  const pendingCard = pendingReviewValue(staffPage);
  await expect(pendingCard).not.toHaveText("—");
  const initialPending = Number(await pendingCard.textContent());

  // Session 2: a guest, in a completely separate browser session (its own
  // cookies/local storage - no shared state with session 1), opens the
  // public join link and queues up.
  const guestContext = await browser.newContext();
  const guestPage = await guestContext.newPage();
  await guestPage.goto("/join");

  const guestName = `Playwright E2E Guest ${Date.now()}`;
  await guestPage.getByLabel("Name for the party").fill(guestName);
  await guestPage.getByLabel("Party size").fill("2");
  await guestPage.getByLabel("Mobile number").fill("+61 400 123 456");
  await guestPage.getByLabel("I have read and accept the waitlist policy").check();
  await guestPage.getByRole("button", { name: "Join waitlist" }).click();

  await expect(guestPage.getByRole("heading", { name: "You're on the waitlist" })).toBeVisible();
  const ticketCode = (await guestPage.locator(".ticket-code").innerText()).trim();
  expect(ticketCode).toMatch(/^A-/);

  // Back on session 1: no reload, no click yet - just wait for the
  // dashboard's own 20s poll to pick up the new pending entry.
  await expect(pendingCard).toHaveText(String(initialPending + 1), { timeout: 25_000 });

  // The entries list isn't on a polling timer, so bring it up to date the
  // same way staff would, and confirm the new guest is now visible.
  await staffPage.getByRole("button", { name: "Refresh" }).click();
  const entryRow = staffPage.locator("article", { hasText: guestName });
  await expect(entryRow).toBeVisible();
  await expect(entryRow).toContainText(ticketCode);

  await staffContext.close();
  await guestContext.close();
});
