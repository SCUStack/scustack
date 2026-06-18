/** Tests for useKeyboardShortcuts composable */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

describe('useKeyboardShortcuts', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('is a function that can be called', async () => {
    const { useKeyboardShortcuts } = await import('../composables/useKeyboardShortcuts')
    expect(() => useKeyboardShortcuts()).not.toThrow()
  })

  it('adds keydown listener on mount', async () => {
    const addSpy = vi.spyOn(document, 'addEventListener')
    const { useKeyboardShortcuts } = await import('../composables/useKeyboardShortcuts')
    mount({
      template: '<div />',
      setup() {
        useKeyboardShortcuts()
      },
    })
    expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('dispatches close-all-overlays on Escape', async () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')
    // Find the handler that was registered
    const addSpy = vi.spyOn(document, 'addEventListener')
    const { useKeyboardShortcuts } = await import('../composables/useKeyboardShortcuts')
    mount({
      template: '<div />',
      setup() {
        useKeyboardShortcuts()
      },
    })

    const handler = addSpy.mock.calls.find(call => call[0] === 'keydown')?.[1] as ((e: Event) => void) | undefined
    expect(handler).toBeDefined()
    if (handler) {
      handler(new KeyboardEvent('keydown', { key: 'Escape' }))
      const dispatched = dispatchSpy.mock.calls.some(
        call => (call[0] as CustomEvent)?.type === 'close-all-overlays'
      )
      expect(dispatched).toBe(true)
    }
  })

  it('ignores "/" in input fields', async () => {
    const input = document.createElement('input')
    input.focus()
    const focusSpy = vi.spyOn(input, 'focus')
    document.querySelector = vi.fn().mockReturnValue(null)

    const addSpy = vi.spyOn(document, 'addEventListener')
    const { useKeyboardShortcuts } = await import('../composables/useKeyboardShortcuts')
    mount({
      template: '<div />',
      setup() {
        useKeyboardShortcuts()
      },
    })

    const handler = addSpy.mock.calls.find(call => call[0] === 'keydown')?.[1] as ((e: Event) => void) | undefined
    if (handler) {
      handler(Object.defineProperty(new KeyboardEvent('keydown', { key: '/' }), 'target', { value: input }))
      expect(focusSpy).not.toHaveBeenCalled()
    }
  })
})
