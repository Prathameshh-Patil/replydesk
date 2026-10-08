import { expect, type Page, test } from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://localhost:8020";
const STAFF = { email: "e2e@replydesk.dev", password: "e2e-password-123" };

async function logIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(STAFF.email);
  await page.getByLabel("Password").fill(STAFF.password);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
}

test("staff can log in and approve a drafted reply", async ({ page, request }) => {
  // A customer message arrives through the API; the (fake) agents draft a reply.
  const subject = `Late order ${Date.now()}`;
  const created = await request.post(`${API}/tickets`, {
    data: { customer_name: "Asha", customer_email: "asha@example.com", subject,
            body: "My order PP-704001 has not arrived." },
  });
  const { id } = await created.json();

  await logIn(page);
  await page.getByRole("link", { name: subject }).click(); // it's in the "To review" inbox
  await expect(page.getByRole("heading", { name: `#${id} ${subject}` })).toBeVisible();
  await expect(page.getByLabel(/Draft reply/)).toHaveValue(/Team Pixel & Plug/);

  await page.getByRole("button", { name: "Approve", exact: true }).click();

  await expect(page.getByText("Approved without edits")).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve", exact: true })).toBeDisabled();
});

test("a customer message moves through all four steps and reaches review", async ({ page }) => {
  const subject = `Refund please ${Date.now()}`;
  await page.goto("/new");
  await page.getByLabel("Your name").fill("Ravi");
  await page.getByLabel("Your email").fill("ravi@example.com");
  await page.getByLabel("Subject").fill(subject);
  await page.getByLabel("Message").fill("I returned my earbuds, order PP-704002. Where is my refund?");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByRole("heading", { name: "Message received" })).toBeVisible();
  const ticketUrl = await page.getByRole("link", { name: /Watch it/ }).getAttribute("href");

  await logIn(page);
  await page.goto(ticketUrl!);

  await expect(page.getByText("ready for review", { exact: true })).toBeVisible();
  for (const step of ["sorter", "extractor", "drafter", "checker"]) {
    await expect(page.getByText(step, { exact: true })).toBeVisible();
  }
  await expect(page.getByText("step 4 of 4")).toBeVisible();
});
