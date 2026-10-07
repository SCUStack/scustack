import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { getMobilePageTitle } from '../utils/mobileNavigation'

const root = resolve(import.meta.dirname, '..')

describe('mobile core navigation', () => {
  it('maps core route paths to stable mobile titles', () => {
    expect(getMobilePageTitle('/search')).toBe('资料搜索')
    expect(getMobilePageTitle('/course/123')).toBe('课程详情')
    expect(getMobilePageTitle('/material/123')).toBe('资料详情')
    expect(getMobilePageTitle('/upload')).toBe('贡献资料')
    expect(getMobilePageTitle('/user/profile')).toBe('个人中心')
  })
  it('provides a shared page header with back and search actions', () => {
    const header = readFileSync(resolve(root, 'components/mobile/MobilePageHeader.vue'), 'utf8')
    expect(header).toContain('aria-label="返回上一页"')
    expect(header).toContain('to="/search"')
    expect(header).toContain('min-h-[44px]')
  })

  it('renders the shared header and reserves space on every non-home mobile route', () => {
    const layout = readFileSync(resolve(root, 'layouts/default.vue'), 'utf8')
    expect(layout).toContain('<MobilePageHeader v-if="!isHome"')
    expect(layout).toContain('var(--mobile-header-height)')
    expect(layout).toContain('route.meta.title')
  })
})
