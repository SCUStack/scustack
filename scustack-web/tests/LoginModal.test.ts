import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const closeLogin = vi.fn()
const loginWithPassword = vi.fn()
const registerWithPassword = vi.fn()

vi.stubGlobal('useAuthStore', () => ({
  isLoginModalOpen: true,
  closeLogin,
  loginWithPassword,
  registerWithPassword,
}))

describe('LoginModal', () => {
  beforeEach(() => {
    closeLogin.mockClear()
    loginWithPassword.mockReset()
    registerWithPassword.mockReset()
  })

  it('exposes dialog semantics and closes from Escape', async () => {
    const { default: LoginModal } = await import('../components/auth/LoginModal.vue')
    const wrapper = mount(LoginModal, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' },
        },
      },
    })

    const dialog = wrapper.get('[role="dialog"]')
    expect(dialog.attributes('aria-modal')).toBe('true')
    expect(dialog.attributes('aria-labelledby')).toBe('login-modal-title')
    expect(wrapper.get('button[aria-label="关闭"]').exists()).toBe(true)

    await dialog.trigger('keydown.esc')
    expect(closeLogin).toHaveBeenCalledOnce()
  })

  it('shows student-id login and university verification registration', async () => {
    const { default: LoginModal } = await import('../components/auth/LoginModal.vue')
    const wrapper = mount(LoginModal, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' },
        },
      },
    })

    expect(wrapper.get('#login-university-id').attributes('autocomplete')).toBe('username')
    expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('短信登录')

    await wrapper.get('#auth-tab-register').trigger('click')
    expect(wrapper.find('#university-password').exists()).toBe(true)
    expect(wrapper.find('#register-password').exists()).toBe(true)
    expect(wrapper.text()).toContain('川大密码不会保存')
  })

  it('clears the university password after a failed registration attempt', async () => {
    registerWithPassword.mockRejectedValueOnce({
      response: { _data: { message: '川大身份校验服务暂不可用' } },
    })
    const { default: LoginModal } = await import('../components/auth/LoginModal.vue')
    const wrapper = mount(LoginModal, {
      global: {
        stubs: {
          AppIcon: { template: '<span />' },
          NuxtLink: { template: '<a><slot /></a>' },
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' },
        },
      },
    })

    await wrapper.get('#auth-tab-register').trigger('click')
    await wrapper.get('#register-university-id').setValue('2026123456789')
    await wrapper.get('#university-password').setValue('school-secret')
    await wrapper.get('#register-password').setValue('local-pass-1')
    await wrapper.get('#confirm-password').setValue('local-pass-1')
    await wrapper.get('input[type="checkbox"]').setValue(true)
    await wrapper.get('#auth-panel-register').trigger('submit')
    await flushPromises()

    expect(registerWithPassword).toHaveBeenCalledWith(
      '2026123456789',
      'school-secret',
      'local-pass-1',
      'local-pass-1',
    )
    expect((wrapper.get('#university-password').element as HTMLInputElement).value).toBe('')
    expect(wrapper.text()).toContain('川大身份校验服务暂不可用')
  })
})
