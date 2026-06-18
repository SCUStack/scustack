/** Tests for useToast composable */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

describe('useToast', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a success toast', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.success('操作成功')
    expect(toast.toasts.value).toHaveLength(1)
    expect(toast.toasts.value[0].message).toBe('操作成功')
    expect(toast.toasts.value[0].type).toBe('success')
  })

  it('adds an error toast', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.error('操作失败')
    expect(toast.toasts.value[0].type).toBe('error')
    expect(toast.toasts.value[0].message).toBe('操作失败')
  })

  it('adds a warning toast', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.warning('请注意')
    expect(toast.toasts.value[0].type).toBe('warning')
  })

  it('adds an info toast', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.info('提示信息')
    expect(toast.toasts.value[0].type).toBe('info')
  })

  it('auto-dismisses toasts after timeout', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.success('test')
    expect(toast.toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(3000)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('limits visible toasts to max 3', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.success('1')
    toast.success('2')
    toast.success('3')
    toast.success('4')
    expect(toast.toasts.value).toHaveLength(3)
    expect(toast.toasts.value[0].message).toBe('2')
  })

  it('removes toast by id', async () => {
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    toast.success('removable')
    const id = toast.toasts.value[0].id
    toast.remove(id)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('returns read-only toasts', async () => {
    const { isReadonly } = await import('vue')
    const { useToast } = await import('../composables/useToast')
    const toast = useToast()
    expect(toast.toasts).toBeDefined()
    expect(isReadonly(toast.toasts)).toBe(true)
  })
})
