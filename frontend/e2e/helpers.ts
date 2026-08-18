import { execSync } from "node:child_process";

/**
 * Without SMTP configured (the default - see backend/app/email.py),
 * verification/reset codes are only logged by the backend, never actually
 * emailed. This reads the most recently logged code of the given kind
 * straight out of `docker compose logs`, the same way this whole feature
 * was manually verified throughout development.
 *
 * "verify" covers both the initial signup verification and an email-change
 * verification - the backend logs the identical phrase for both purposes
 * (see PURPOSE_VERIFY_EMAIL / PURPOSE_CHANGE_EMAIL in email.py), so grabbing
 * the latest match is always the code for whichever action was just
 * triggered, as long as tests run serially (they do - see playwright.config.ts).
 */
export function getLatestCode(kind: "verify" | "reset"): string {
  const logs = execSync("docker compose logs backend --tail 200", {
    cwd: "..",
    encoding: "utf-8",
  });
  const pattern =
    kind === "reset" ? /Your reset code is: (\d{6})/g : /Your verification code is: (\d{6})/g;
  const matches = [...logs.matchAll(pattern)];
  if (matches.length === 0) {
    throw new Error(`No "${kind}" code found in backend logs - was it actually sent?`);
  }
  return matches[matches.length - 1][1];
}

/** Unique per test run so re-running locally against a persistent DB doesn't collide. */
export function uniqueSuffix(): string {
  return Date.now().toString(36);
}
