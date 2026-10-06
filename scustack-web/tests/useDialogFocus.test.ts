import { mount } from '@vue/test-utils'
import { defineComponent, nextTick, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useDialogFocus } from '~/composables/useDialogFocus'

describe('useDialogFocus', () => {
  it('focuses the first control, traps Tab, closes on Escape, and restores focus', async () => {
    const trigger = document.createElement('button')
    document.body.append(trigger)
    trigger.focus()
    const closed = vi.fn()
    const wrapper = mount(defineComponent({
      setup() {
        const open = ref(false)
        const dialog = ref<HTMLElement | null>(null)
        useDialogFocus(open, dialog, () => { open.value = false; closed() })
        return { open, dialog }
      },
      template: '<div v-if="open" ref="dialog" tabindex="-1"><button>第一个</button><button>最后一个</button></div>',
    }))

    wrapper.vm.open = true
    await nextTick()
    await nextTick()
    expect(document.activeElement?.textContent).toBe('第一个')

    const buttons = wrapper.findAll('button')
    buttons[1].element.focus()
    buttons[1].element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))
    expect(document.activeElement?.textContent).toBe('第一个')

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(closed).toHaveBeenCalledOnce()
    await nextTick()
    expect(document.activeElement).toBe(trigger)

    trigger.remove()
    wrapper.unmount()
  })
})
