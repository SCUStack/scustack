/** Tests for useToast composable */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useToast } from '../composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllTimers()
  })

  it('adds a success toast', () => {
    const toast = useToast()
    toast.success('操作成功')
    expect(toast.toasts.value).toHaveLength(1)
    expect(toast.toasts.value[0].message).toBe('操作成功')
    expect(toast.toasts.value[0].type).toBe('success')
  })

  it('adds an error toast', () => {
    const toast = useToast()
    toast.error('操作失败')
    expect(toast.toasts.value[0].type).toBe('error')
    expect(toast.toasts.value[0].message).toBe('操作失败')
  })

  it('adds a warning toast', () => {
    const toast = useToast()
    toast.warning('请注意')
    expect(toast.toasts.value[0].type).toBe('warning')
  })

  it('adds an info toast', () => {
    const toast = useToast()
    toast.info('提示信息')
    expect(toast.toasts.value[0].type).toBe('info')
  })

  it('auto-dismisses toasts after timeout', () => {
    const toast = useToast()
    toast.success('test')
    expect(toast.toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(3000)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('limits visible toasts to max 3', () => {
    const toast = useToast()
    toast.success('1')
    toast.success('2')
    toast.success('3')
    toast.success('4')
    expect(toast.toasts.value).toHaveLength(3)
    expect(toast.toasts.value[0].message).toBe('2')
  })

  it('removes toast by id', () => {
    const toast = useToast()
    toast.success('removable')
    const id = toast.toasts.value[0].id
    toast.remove(id)
    expect(toast.toasts.value).toHaveLength(0)
  })

  it('returns read-only toasts', () => {
    const toast = useToast()
    expect(toast.toasts).toBeDefined()
    // Should be readonly — cannot assign
    const descriptor = Object.getOwnPropertyDescriptor(toast, 'toasts')
    expect(descriptor?.writable).toBeFalsy()
  })
})
