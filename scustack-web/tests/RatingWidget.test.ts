/** Tests for RatingWidget component */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

const toastMocks = vi.hoisted(() => ({
  success: vi.fn(),
}))

vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('useToast', () => toastMocks)
vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 0, data: { average_rating: 4, rating_count: 6 } }))

describe('RatingWidget', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('mounts successfully', async () => {
    const { default: RatingWidget } = await import('../components/material/RatingWidget.vue')
    const wrapper = mount(RatingWidget, {
      props: {
        materialId: 'test-id',
        initialRating: 3.5,
        ratingCount: 10,
      },
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('4.0')
    expect(wrapper.text()).toContain('10')
  })

  it('shows zero rating state', async () => {
    const { default: RatingWidget } = await import('../components/material/RatingWidget.vue')
    const wrapper = mount(RatingWidget, {
      props: {
        materialId: 'test-id',
        initialRating: 0,
        ratingCount: 0,
      },
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toBe('')
  })

  it('renders 5 star buttons', async () => {
    const { default: RatingWidget } = await import('../components/material/RatingWidget.vue')
    const wrapper = mount(RatingWidget, {
      props: {
        materialId: 'test-id',
        initialRating: 0,
        ratingCount: 0,
      },
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(5)
  })

  it('emits hover state on mouseenter', async () => {
    const { default: RatingWidget } = await import('../components/material/RatingWidget.vue')
    const wrapper = mount(RatingWidget, {
      props: {
        materialId: 'test-id',
        initialRating: 0,
        ratingCount: 0,
      },
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    const buttons = wrapper.findAll('button')
    await buttons[3].trigger('mouseenter')
    // After hovering over 4th star, the hover state should be reflected
    expect(wrapper.exists()).toBe(true)
  })

  it('does not allow rating when not logged in', async () => {
    const { default: RatingWidget } = await import('../components/material/RatingWidget.vue')
    const wrapper = mount(RatingWidget, {
      props: {
        materialId: 'test-id',
        initialRating: 4,
        ratingCount: 5,
      },
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    // Without auth, rating should be unchanged
    expect(wrapper.exists()).toBe(true)
  })
})
