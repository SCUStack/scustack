export function useWatermark() {
  function getWatermarkText(): string {
    const auth = useAuthStore()
    const uid = auth.user?.id?.slice(-8) || 'guest'
    const date = new Date().toISOString().slice(0, 10)
    return `${uid} · ${date}`
  }

  function createWatermarkStyle(): Record<string, string> {
    const text = getWatermarkText()
    const encoded = btoa(unescape(encodeURIComponent(text)))
    return {
      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='60'%3E%3Ctext x='150' y='30' text-anchor='middle' fill='rgba(0,0,0,0.06)' font-size='12' font-family='sans-serif'%3E${encoded}%3C/text%3E%3C/svg%3E")`,
      backgroundRepeat: 'repeat',
      pointerEvents: 'none',
    }
  }

  function canvasWatermark(ctx: CanvasRenderingContext2D, width: number, height: number) {
    const text = getWatermarkText()
    ctx.save()
    ctx.fillStyle = 'rgba(0, 0, 0, 0.06)'
    ctx.font = '14px sans-serif'
    const metrics = ctx.measureText(text)
    const tw = metrics.width + 60
    const cols = Math.ceil(width / tw)
    const rows = Math.ceil(height / 50)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        ctx.fillText(text, c * tw, r * 50 + 30)
      }
    }
    ctx.restore()
  }

  const watermarkStyle = computed(() => createWatermarkStyle())

  return { getWatermarkText, canvasWatermark, watermarkStyle }
}
