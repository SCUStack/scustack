import { nextTick, onUnmounted, watch, type Ref } from 'vue'

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

export function useDialogFocus(
  isOpen: Ref<boolean>,
  dialogRef: Ref<HTMLElement | null>,
  close: () => void,
) {
  let restoreTarget: HTMLElement | null = null

  function focusableElements() {
    const nodes = dialogRef.value?.querySelectorAll<HTMLElement>(focusableSelector)
    return nodes ? [...nodes] : []
  }

  function onKeydown(event: KeyboardEvent) {
    if (!isOpen.value) return
    if (event.key === 'Escape') {
      event.preventDefault()
      close()
      return
    }
    if (event.key !== 'Tab') return

    const elements = focusableElements()
    if (!elements.length) {
      event.preventDefault()
      dialogRef.value?.focus()
      return
    }

    const first = elements[0]
    const last = elements[elements.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  function focusDialog() {
    void nextTick().then(() => {
      const first = focusableElements()[0]
      ;(first || dialogRef.value)?.focus()
    })
  }

  function onOpen(open: boolean) {
    if (open) {
      restoreTarget = document.activeElement instanceof HTMLElement ? document.activeElement : null
      document.addEventListener('keydown', onKeydown)
      void focusDialog()
    } else {
      document.removeEventListener('keydown', onKeydown)
      restoreTarget?.focus()
      restoreTarget = null
    }
  }

  watch(isOpen, onOpen)
  onUnmounted(() => {
    document.removeEventListener('keydown', onKeydown)
    restoreTarget = null
  })

  return { focusDialog }
}
