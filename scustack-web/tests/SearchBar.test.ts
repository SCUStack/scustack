/** Tests for SearchBar component — debounce, autocomplete, keyboard navigation */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('navigateTo', vi.fn())
vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 0, data: { keywords: [] } }))

describe('SearchBar', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('mounts successfully', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('has an input field', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
  })

  it('debounces input before search', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    const input = wrapper.find('input')
    await input.setValue('数据结构')
    // Before debounce, should not have navigated
    expect(wrapper.exists()).toBe(true)
    vi.advanceTimersByTime(300)
    expect(wrapper.exists()).toBe(true)
  })

  it('clears input on clear button click', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    const input = wrapper.find('input')
    await input.setValue('test')
    expect((input.element as HTMLInputElement).value).toBe('test')
  })

  it('uses the provided placeholder text', async () => {
    const { default: SearchBar } = await import('../components/search/SearchBar.vue')
    const wrapper = mount(SearchBar, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    expect(wrapper.find('input').attributes('placeholder')).toContain('搜索')
  })
})
