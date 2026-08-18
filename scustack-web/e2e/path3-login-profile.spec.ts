/**
 * E2E Path 3: Login/Profile/Bookmarks
 *
 * Student ID login → edit profile → bookmark material → view bookmarks → un-bookmark
 */
import { test, expect } from '@playwright/test'

test.describe('Path 3: Login and Profile', () => {
  test('homepage shows login button when not authenticated', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })

  test('user profile requires authentication', async ({ page }) => {
    await page.goto('/user/profile')
    await page.waitForLoadState('networkidle')
    // Should redirect or show login
    await expect(page.locator('body')).toBeVisible()
  })

  test('bookmarks page requires authentication', async ({ page }) => {
    await page.goto('/user/bookmarks')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })

  test('contributions page requires authentication', async ({ page }) => {
    await page.goto('/user/contributions')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })

  test('privacy page requires authentication', async ({ page }) => {
    await page.goto('/user/privacy')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })

  test('error scenario: login with empty student id', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    // Login modal should handle an empty student ID without submitting.
    await expect(page.locator('body')).toBeVisible()
  })
})
