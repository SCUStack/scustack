import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const toastMocks = vi.hoisted(() => ({
  success: vi.fn(),
}))

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('useToast', () => toastMocks)
vi.stubGlobal('defineNuxtPlugin', (plugin: unknown) => plugin)

async function mountComponent() {
  const { default: FeedbackButton } = await import('../components/common/FeedbackButton.vue')
  return mount(FeedbackButton, {
    attachTo: document.body,
    global: {
      stubs: {
        AppIcon: { template: '<span />' },
        Teleport: true,
      },
    },
  })
}

function findSubmitButton(wrapper: Awaited<ReturnType<typeof mountComponent>>) {
  return wrapper.findAll('button').find((button) => button.text().includes('提交反馈'))
}

describe('FeedbackButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows backend error when feedback submission fails', async () => {
    vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 40000, message: '提交失败' }))
    const wrapper = await mountComponent()

    await wrapper.find('button[aria-label="反馈"]').trigger('click')
    await wrapper.find('textarea').setValue('反馈内容')
    await findSubmitButton(wrapper)?.trigger('click')

    await new Promise(resolve => setTimeout(resolve))
    expect(wrapper.text()).toContain('提交失败')
    expect(toastMocks.success).not.toHaveBeenCalled()
  })

  it('resets form and shows success toast after successful submit', async () => {
    vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({ code: 0, message: 'ok' }))
    const wrapper = await mountComponent()

    await wrapper.find('button[aria-label="反馈"]').trigger('click')
    await wrapper.find('textarea').setValue('反馈内容')
    await wrapper.find('input[type="email"]').setValue('test@example.com')
    await findSubmitButton(wrapper)?.trigger('click')

    await new Promise(resolve => setTimeout(resolve))
    expect(toastMocks.success).toHaveBeenCalledWith('感谢反馈！')
    expect(wrapper.text()).not.toContain('反馈内容')
  })
})
