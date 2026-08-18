import { expect, test } from '@playwright/test'

const apiBase = 'http://localhost:8403'

test('public API release gates are healthy', async ({ request }) => {
  for (const path of ['/api/v1/health', '/api/v1/health/live', '/api/v1/health/ready']) {
    const response = await request.get(`${apiBase}${path}`)
    expect(response.status(), path).toBe(200)
  }

  for (const path of [
    '/api/v1/homepage',
    '/api/v1/homepage/recent-updates?limit=5',
    '/api/v1/search?q=%E9%AB%98%E7%AD%89%E6%95%B0%E5%AD%A6&page=1&page_size=20',
  ]) {
    const response = await request.get(`${apiBase}${path}`)
    expect(response.status(), path).toBe(200)
    expect((await response.json()).code, path).toBe(0)
  }
})

test('anonymous search challenge is visible in admin security monitoring', async ({ page }) => {
  const identity = `release-gate-${Date.now()}`
  const headers = {
    'User-Agent': identity,
    'Accept-Language': 'zh-CN',
    'X-Forwarded-For': '198.51.100.78',
  }

  await page.request.get(`${apiBase}/api/v1/search?q=&page=20&page_size=50`, { headers })

  let challengeCode: number | undefined
  for (let pageNumber = 21; pageNumber <= 25 && challengeCode !== 42920; pageNumber += 1) {
    const response = await page.request.get(
      `${apiBase}/api/v1/search?q=&page=${pageNumber}&page_size=50`,
      { headers },
    )
    challengeCode = (await response.json()).code
  }
  expect(challengeCode).toBe(42920)

  const loginResponse = await page.request.post(`${apiBase}/api/v1/auth/login`, {
    data: { university_id: '20260000000', password: '123456' },
  })
  expect(loginResponse.status()).toBe(200)
  expect((await loginResponse.json()).code).toBe(0)

  await page.goto('/admin/security')
  await expect(page.getByRole('heading', { name: '安全监控' })).toBeVisible()
  await expect(page.getByText('搜索验证触发').first()).toBeVisible()
  await expect(page.getByText('search_query').first()).toBeVisible()
})

test('common controls support keyboard dismissal and mobile search input', async ({ page }) => {
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const searchInput = page.getByRole('combobox').first()
  await expect(searchInput).toHaveAttribute('enterkeyhint', 'search')
  await expect(searchInput).toHaveAttribute('autocomplete', 'off')

  await page.getByRole('button', { name: /未登录|登录或注册/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
})
