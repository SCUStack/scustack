export function useFullscreen() {
  const isFullscreen = ref(false)

  function enter() {
    isFullscreen.value = true
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeydown)
  }

  function exit() {
    isFullscreen.value = false
    document.body.style.overflow = ''
    document.removeEventListener('keydown', onKeydown)
  }

  function toggle() {
    if (isFullscreen.value) exit()
    else enter()
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      exit()
      return
    }
    if (e.key === 'f' || e.key === 'F') {
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      e.preventDefault()
      exit()
    }
  }

  onUnmounted(() => {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', onKeydown)
  })

  return { isFullscreen, enter, exit, toggle }
}
