import { describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount } from '@vue/test-utils'
import { axe } from 'vitest-axe'

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('navigateTo', vi.fn())
vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 0, data: [] }))

describe('a11y baseline', () => {
  it('SearchBar has no obvious axe violations', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await wrapper.find('input').setValue('数据结构')
    const host = document.createElement('main')
    host.appendChild(wrapper.element)
    const results = await axe(host)
    expect(results.violations).toHaveLength(0)
  })

  it('profile edit dialog keeps explicit dialog semantics', () => {
    const source = readFileSync(resolve(__dirname, '../pages/user/profile.vue'), 'utf-8')
    expect(source).toContain('role="dialog"')
    expect(source).toContain('aria-modal="true"')
    expect(source).toContain('aria-label="编辑个人资料"')
  })

  it('announcements create dialog keeps explicit dialog semantics', () => {
    const source = readFileSync(resolve(__dirname, '../pages/admin/announcements.vue'), 'utf-8')
    expect(source).toContain('role="dialog"')
    expect(source).toContain('aria-modal="true"')
    expect(source).toContain('aria-label="新建全站通知"')
  })

  it('homepage banner controls keep accessible labels', () => {
    const source = readFileSync(resolve(__dirname, '../pages/index.vue'), 'utf-8')
    expect(source).toContain('aria-label="首页横幅轮播"')
    expect(source).toContain(':aria-label="`切换到第 ${idx + 1} 个首页横幅`"')
  })
})
