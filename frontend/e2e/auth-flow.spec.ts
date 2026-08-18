import { test, expect } from "@playwright/test";
import { getLatestCode, uniqueSuffix } from "./helpers";

// One long test with named steps, sharing a single page/session throughout -
// rather than separate test() blocks, which each get a fresh browser
// context (no shared localStorage/session) by default. Registering a fresh
// account is also rate-limited (5/hour/IP - see playwright.config.ts), so
// reusing one account across the whole flow mirrors how it was manually
// verified throughout development anyway.

const suffix = uniqueSuffix();
const username = `e2e_${suffix}`;
const newUsername = `e2e_${suffix}_renamed`;
const email = `e2e_${suffix}@example.com`;
const newEmail = `e2e_${suffix}_new@example.com`;
const password = "e2e-test-pass-1";
const newPassword = "e2e-test-pass-2";

test("full account lifecycle: signup, verify, rename, reset password, delete", async ({ page }) => {
  await test.step("sign up", async () => {
    await page.goto("/signup");
    await page.getByPlaceholder("Username").fill(username);
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password (min. 8 characters)").fill(password);
    await page.getByRole("button", { name: "Create Account" }).click();

    // Immediate-use is allowed even unverified - lands on the dashboard.
    await expect(page).toHaveURL("/");
    await expect(page.getByRole("link", { name: "Verify email" })).toBeVisible();
  });

  await test.step("verify email", async () => {
    await page.getByRole("link", { name: "Verify email" }).click();
    await expect(page).toHaveURL("/verify-email");

    const code = getLatestCode("verify");
    await page.getByPlaceholder("123456").fill(code);
    await page.getByRole("button", { name: "Confirm" }).click();

    await expect(page.getByText(/is verified/)).toBeVisible();
    await expect(page.getByRole("link", { name: "Verify email" })).toHaveCount(0);
  });

  await test.step("change username and email together", async () => {
    await page.goto("/account");
    await page.getByLabel("Username").fill(newUsername);
    await page.getByLabel("Email").fill(newEmail);
    await page.getByLabel("Current password (required to confirm)").fill(password);
    await page.getByRole("button", { name: "Save" }).click();

    await expect(page.getByText("Changes saved.")).toBeVisible();
    // Username applies immediately; nav reflects it.
    await expect(page.getByRole("link", { name: newUsername })).toBeVisible();
    // Email does not - it's pending until confirmed.
    await expect(page.getByText(newEmail, { exact: false })).toBeVisible();
    await expect(page.getByLabel("Email")).toHaveValue(email);
  });

  await test.step("confirm the pending email change", async () => {
    await page.goto("/verify-email");
    await expect(page.getByText(newEmail, { exact: false })).toBeVisible();

    const code = getLatestCode("verify");
    await page.getByPlaceholder("123456").fill(code);
    await page.getByRole("button", { name: "Confirm" }).click();

    await expect(page.getByText(/is verified/)).toBeVisible();

    await page.goto("/account");
    await expect(page.getByLabel("Email")).toHaveValue(newEmail);
  });

  await test.step("log out and log back in with the new email", async () => {
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL("/login");

    await page.getByPlaceholder("Email").fill(newEmail);
    await page.getByPlaceholder("Password").fill(password);
    await page.getByRole("button", { name: "Log In" }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("link", { name: newUsername })).toBeVisible();
  });

  await test.step("log out, then reset the password via email", async () => {
    await page.getByRole("button", { name: "Log out" }).click();

    await page.goto("/forgot-password");
    await page.getByPlaceholder("Email").fill(newEmail);
    await page.getByRole("button", { name: "Send reset code" }).click();
    await expect(page.getByText(/reset code has been sent/)).toBeVisible();

    await page.getByRole("link", { name: "I have a code" }).click();
    await expect(page).toHaveURL(new RegExp(`/reset-password\\?email=${encodeURIComponent(newEmail)}`));

    const code = getLatestCode("reset");
    await page.getByPlaceholder("6-digit code").fill(code);
    await page.getByPlaceholder("New password (min. 8 characters)").fill(newPassword);
    await page.getByPlaceholder("Confirm new password").fill(newPassword);
    await page.getByRole("button", { name: "Reset password" }).click();

    await expect(page.getByText(/password has been reset/i)).toBeVisible();
  });

  await test.step("log in with the new password and delete the account", async () => {
    await page.goto("/login");
    await page.getByPlaceholder("Email").fill(newEmail);
    await page.getByPlaceholder("Password").fill(newPassword);
    await page.getByRole("button", { name: "Log In" }).click();
    await expect(page).toHaveURL("/");

    await page.goto("/account");
    await page.getByLabel("Current password", { exact: true }).fill(newPassword);
    await page.getByRole("button", { name: "Delete account permanently" }).click();
    await page.getByRole("button", { name: "Delete permanently" }).click();

    await expect(page).toHaveURL("/login");

    // Account is really gone - logging in again must fail.
    await page.getByPlaceholder("Email").fill(newEmail);
    await page.getByPlaceholder("Password").fill(newPassword);
    await page.getByRole("button", { name: "Log In" }).click();
    await expect(page.getByText(/incorrect/i)).toBeVisible();
  });
});

test("legal pages are reachable without logging in", async ({ page }) => {
  await page.goto("/impressum");
  await expect(page.getByRole("heading", { name: "Impressum" })).toBeVisible();

  await page.goto("/datenschutz");
  await expect(page.getByRole("heading", { name: "Datenschutzerklärung" })).toBeVisible();
});
