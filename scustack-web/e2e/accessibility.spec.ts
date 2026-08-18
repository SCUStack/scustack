import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { expect, test, type Page } from '@playwright/test'
import type { AxeResults } from 'axe-core'

const require = createRequire(import.meta.url)
const axeSource = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8')

const publicRoutes = [
  { name: 'home', path: '/' },
  { name: 'search', path: '/search?q=%E9%AB%98%E7%AD%89%E6%95%B0%E5%AD%A6' },
  { name: 'courses', path: '/course' },
  { name: 'colleges', path: '/colleges' },
  { name: 'about', path: '/about' },
  { name: 'copyright', path: '/copyright' },
  { name: 'privacy', path: '/privacy' },
  { name: 'terms', path: '/terms' },
  { name: 'not-found', path: '/route-that-does-not-exist' },
]

const authenticatedRoutes = [
  '/upload',
  '/user/profile',
  '/user/bookmarks',
  '/user/contributions',
  '/user/privacy',
  '/admin/review',
  '/admin/materials',
  '/admin/reports',
  '/admin/analytics',
  '/admin/security',
  '/admin/storage',
]

type ReportedViolation = Pick<AxeResults['violations'][number], 'id' | 'impact' | 'help'> & {
  targets: AxeResults['violations'][number]['nodes'][number]['target'][]
}

async function scanPage(page: Page): Promise<ReportedViolation[]> {
  await page.waitForLoadState('networkidle')
  await page.addScriptTag({ content: axeSource })
  const results = await page.evaluate<AxeResults>(async () => {
    return await window.axe.run(document, {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa'],
      },
    })
  })

  return results.violations.map(({ id, impact, help, nodes }) => ({
    id,
    impact,
    help,
    targets: nodes.map((node) => node.target),
  }))
}

for (const route of publicRoutes) {
  test(`${route.name} has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto(route.path)
    expect(await scanPage(page)).toEqual([])
  })
}

test('dynamic public detail pages have no WCAG A/AA violations', async ({ page }) => {
  test.setTimeout(90_000)
  const violationsByRoute: Record<string, ReportedViolation[]> = {}

  await page.goto('/colleges')
  const collegePath = await page.locator('a[href^="/colleges/"]').first().getAttribute('href')
  expect(collegePath).toBeTruthy()
  await page.goto(collegePath!)
  violationsByRoute[collegePath!] = await scanPage(page)

  await page.goto('/course')
  const coursePath = await page.locator('a[href^="/course/"]').first().getAttribute('href')
  expect(coursePath).toBeTruthy()
  await page.goto(coursePath!)
  violationsByRoute[coursePath!] = await scanPage(page)

  await page.goto('/search?q=%E9%AB%98%E7%AD%89%E6%95%B0%E5%AD%A6')
  const materialPath = await page.locator('a[href^="/material/"]').first().getAttribute('href')
  expect(materialPath).toBeTruthy()
  await page.goto(materialPath!)
  violationsByRoute[materialPath!] = await scanPage(page)

  expect(violationsByRoute).toEqual(Object.fromEntries(Object.keys(violationsByRoute).map((path) => [path, []])))
})

test('authenticated user and maintainer pages have no WCAG A/AA violations', async ({ page }) => {
  test.setTimeout(180_000)
  const loginResponse = await page.request.post('http://localhost:8403/api/v1/auth/login', {
    data: { university_id: '20260000000', password: '123456' },
  })
  expect(loginResponse.ok()).toBeTruthy()
  expect((await loginResponse.json()).code).toBe(0)

  const violationsByRoute: Record<string, ReportedViolation[]> = {}
  for (const route of authenticatedRoutes) {
    await page.goto(route)
    violationsByRoute[route] = await scanPage(page)
  }

  expect(violationsByRoute).toEqual(Object.fromEntries(authenticatedRoutes.map((route) => [route, []])))
})

test('keyboard users can skip directly to the main content', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  const skipLink = page.getByRole('link', { name: '跳到主要内容' })
  await expect(skipLink).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()
})
