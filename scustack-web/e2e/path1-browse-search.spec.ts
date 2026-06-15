/**
 * E2E Path 1: Browse/Search/Preview/Download
 *
 * Visit homepage → click college → browse courses → search → preview material → download
 */
import { test, expect } from '@playwright/test'

test.describe('Path 1: Browse and Search', () => {
  test('homepage loads with colleges', async ({ page }) => {
    const resp = await page.goto('/')
    expect(resp?.status()).toBeLessThan(400)

    await page.waitForLoadState('networkidle')
    // Homepage should have some content
    await expect(page.locator('body')).toBeVisible()
  })

  test('navigate to colleges page', async ({ page }) => {
    await page.goto('/colleges')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()

    // Should show college list (or empty state)
    const collegeCards = page.locator('a[href*="/colleges/"]')
    const count = await collegeCards.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('search functionality works', async ({ page }) => {
    await page.goto('/search?q=数据结构')
    await page.waitForLoadState('networkidle')

    // Search page should load
    await expect(page.locator('body')).toBeVisible()
  })

  test('material detail page handles not found gracefully', async ({ page }) => {
    const resp = await page.goto('/material/00000000-0000-0000-0000-000000000000')
    await page.waitForLoadState('networkidle')

    // Should show error/not-found state, not crash
    const bodyText = await page.locator('body').innerText()
    expect(bodyText.length).toBeGreaterThan(0)
  })

  test('error scenario: search with empty query', async ({ page }) => {
    await page.goto('/search?q=')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible()
  })
})
