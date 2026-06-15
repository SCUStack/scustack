export function useKeyboardShortcuts() {
  function onKeydown(e: KeyboardEvent) {
    if (e.key === '/' && !isInputFocused()) {
      e.preventDefault()
      const searchInput = document.querySelector<HTMLInputElement>(
        'input[type="search"], input[placeholder*="搜索"]',
      )
      searchInput?.focus()
    }

    if (e.key === 'Escape') {
      window.dispatchEvent(new CustomEvent('close-all-overlays'))
    }
  }

  function isInputFocused(): boolean {
    const el = document.activeElement
    if (!el) return false
    const tag = el.tagName.toLowerCase()
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return true
    return (el as HTMLElement).isContentEditable
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))
  onUnmounted(() => document.removeEventListener('keydown', onKeydown))
}
