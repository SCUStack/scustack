export function useWatermark() {
  function getWatermarkText(): string {
    const auth = useAuthStore()
    const uid = auth.user?.id?.slice(-8) || 'guest'
    const now = new Date()
    const ts = now.getFullYear().toString()
      + (now.getMonth() + 1).toString().padStart(2, '0')
      + now.getDate().toString().padStart(2, '0')
      + now.getHours().toString().padStart(2, '0')
      + now.getMinutes().toString().padStart(2, '0')
    return `${uid}-${ts}`
  }

  function createWatermarkStyle(): Record<string, string> {
    const text = getWatermarkText()
    const encoded = btoa(unescape(encodeURIComponent(text)))
    return {
      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='60'%3E%3Ctext x='160' y='30' text-anchor='middle' fill='rgba(0,0,0,0.06)' font-size='12' font-family='sans-serif'%3E${encoded}%3C/text%3E%3C/svg%3E")`,
      backgroundRepeat: 'repeat',
      pointerEvents: 'none',
      userSelect: 'none',
    }
  }

  function canvasWatermark(ctx: CanvasRenderingContext2D, width: number, height: number) {
    const text = getWatermarkText()
    ctx.save()
    ctx.fillStyle = 'rgba(0, 0, 0, 0.06)'
    ctx.font = '14px sans-serif'
    const metrics = ctx.measureText(text)
    const tw = metrics.width + 80
    const cols = Math.ceil(width / tw)
    const rows = Math.ceil(height / 50)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        ctx.fillText(text, c * tw, r * 50 + 30)
      }
    }
    ctx.restore()
  }

  function observeWatermarkCanvas(canvasRef: Ref<HTMLCanvasElement | undefined>, renderFn: () => void) {
    if (typeof MutationObserver === 'undefined') return
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const node of m.removedNodes) {
          if (node === canvasRef.value || (node instanceof Element && canvasRef.value && node.contains(canvasRef.value))) {
            renderFn()
            return
          }
        }
        if (m.type === 'attributes' && m.target === canvasRef.value && m.attributeName === 'style') {
          const style = (m.target as HTMLElement).getAttribute('style') || ''
          if (style.includes('display: none') || style.includes('visibility: hidden')) {
            (m.target as HTMLElement).style.display = ''
            ;(m.target as HTMLElement).style.visibility = ''
          }
        }
      }
    })
    if (canvasRef.value?.parentElement) {
      observer.observe(canvasRef.value.parentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['style'] })
    }
    return observer
  }

  const watermarkStyle = computed(() => createWatermarkStyle())

  return { getWatermarkText, canvasWatermark, observeWatermarkCanvas, watermarkStyle }
}
