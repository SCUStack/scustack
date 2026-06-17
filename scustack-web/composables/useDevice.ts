export function useDevice() {
  const width = ref(1024)

  function update() { width.value = window.innerWidth }
  onMounted(() => { update(); window.addEventListener('resize', update) })
  onUnmounted(() => window.removeEventListener('resize', update))

  const isMobile = computed(() => width.value < 1024)

  return { isMobile, width: readonly(width) }
}
