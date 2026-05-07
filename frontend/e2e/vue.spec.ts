/**
 * Playwright end-to-end tests for the Finance Tracker frontend.
 *
 * Validates that the application boots correctly and the authentication
 * guard redirects unauthenticated users to the login page.
 */
import { test, expect } from '@playwright/test'

/**
 * Verifies that navigating to the root URL redirects to the login page
 * when no authentication token is present.
 */
test('visits the app root url', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/login/)
})
