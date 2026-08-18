import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const toast = {
  success: vi.fn(),
  error: vi.fn(),
}
const writeText = vi.fn().mockResolvedValue(undefined)

vi.stubGlobal('useToast', () => toast)
Object.defineProperty(navigator, 'clipboard', {
  configurable: true,
  value: { writeText },
})

describe('ShareDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows and copies the title, description, and material link', async () => {
    const { default: ShareDialog } = await import('../components/material/ShareDialog.vue')
    const wrapper = mount(ShareDialog, {
      props: {
        modelValue: true,
        materialId: 'material-123',
        title: '数据结构复习资料',
        description: '包含重点章节梳理和期末复习题。',
      },
      attachTo: document.body,
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog?.textContent).toContain('分享内容')
    expect(dialog?.textContent).toContain('包含重点章节梳理和期末复习题。')
    expect(dialog?.textContent).not.toContain('分享口令')

    const copyButton = Array.from(document.body.querySelectorAll('button'))
      .find(button => button.textContent?.includes('复制分享内容')) as HTMLButtonElement
    copyButton.click()
    await vi.waitFor(() => expect(writeText).toHaveBeenCalledOnce())

    expect(writeText).toHaveBeenCalledWith(
      '川流课栈｜数据结构复习资料\n包含重点章节梳理和期末复习题。\n查看资料：http://localhost:3000/material/material-123',
    )
    expect(toast.success).toHaveBeenCalledWith('分享内容已复制')

    wrapper.unmount()
  })

  it('closes when Escape is pressed', async () => {
    const { default: ShareDialog } = await import('../components/material/ShareDialog.vue')
    const wrapper = mount(ShareDialog, {
      props: { modelValue: true, materialId: 'material-123', title: '测试资料' },
      global: {
        stubs: {
          Teleport: true,
          Transition: false,
          AppIcon: { template: '<span />' },
        },
      },
    })

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })
})
