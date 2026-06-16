<template>
  <div class="relative">
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>
    <div v-if="error" class="text-center py-12">
      <p class="text-slate-500 text-sm">{{ error }}</p>
      <a :href="downloadUrl" class="mt-2 inline-block text-sm text-primary-600 hover:text-primary-700">直接下载</a>
    </div>
    <div v-show="!loading && !error" class="relative">
      <div class="flex items-center justify-between mb-3 px-1">
        <div class="flex items-center gap-2">
          <button :disabled="page <= 1" class="px-2 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 cursor-pointer disabled:opacity-30" @click="page--">上一页</button>
          <span class="text-xs text-slate-500">{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" class="px-2 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 cursor-pointer disabled:opacity-30" @click="page++">下一页</button>
        </div>
        <div class="flex items-center gap-2">
          <button class="w-7 h-7 flex items-center justify-center rounded bg-black/30 text-white hover:bg-black/50 cursor-pointer border-none transition-colors" title="全屏预览 (F)" @click="fs.toggle()">
            <AppIcon :name="fs.isFullscreen.value ? 'Minimize2' : 'Maximize2'" :size="14" />
          </button>
          <a :href="downloadUrl" class="text-xs text-primary-600 hover:text-primary-700">下载 PDF</a>
        </div>
      </div>
      <div class="relative border border-slate-200 rounded-lg overflow-hidden bg-slate-100">
        <canvas ref="canvasRef" class="w-full" />
        <canvas ref="watermarkRef" class="absolute inset-0 w-full h-full pointer-events-none" />
      </div>
    </div>

    <!-- Fullscreen overlay -->
    <Teleport to="body">
      <div v-if="fs.isFullscreen.value" class="fixed inset-0 z-[100] bg-white flex flex-col" @click.self="fs.exit()">
        <div class="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white shrink-0">
          <span class="text-sm text-slate-500">{{ page }} / {{ totalPages }}</span>
          <div class="flex items-center gap-2">
            <button :disabled="page <= 1" class="px-2 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 cursor-pointer disabled:opacity-30" @click="page--">上一页</button>
            <button :disabled="page >= totalPages" class="px-2 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 cursor-pointer disabled:opacity-30" @click="page++">下一页</button>
            <button class="w-8 h-8 flex items-center justify-center rounded hover:bg-slate-100 cursor-pointer border-none bg-transparent" title="退出全屏 (Esc)" @click="fs.exit()">
              <AppIcon name="X" :size="18" class="text-slate-500" />
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto flex items-start justify-center p-4 bg-slate-100">
          <canvas ref="fsCanvasRef" class="max-w-full shadow-lg" />
          <canvas ref="fsWatermarkRef" class="absolute inset-0 pointer-events-none" />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ url: string; downloadUrl: string }>()

const canvasRef = ref<HTMLCanvasElement>()
const watermarkRef = ref<HTMLCanvasElement>()
const fsCanvasRef = ref<HTMLCanvasElement>()
const fsWatermarkRef = ref<HTMLCanvasElement>()
const loading = ref(true)
const error = ref('')
const page = ref(1)
const totalPages = ref(0)
let pdfDoc: any = null
let observer: MutationObserver | undefined

const { canvasWatermark, observeWatermarkCanvas } = useWatermark()
const fs = useFullscreen()

onMounted(async () => {
  try {
    const pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`
    const loadingTask = pdfjsLib.getDocument({ url: props.url })
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    await renderPage()
    observer = observeWatermarkCanvas(watermarkRef, renderWatermark)
  } catch {
    error.value = 'PDF 预览加载失败'
  }
  loading.value = false
})

onUnmounted(() => {
  observer?.disconnect()
})

function renderWatermark() {
  if (!watermarkRef.value || !canvasRef.value) return
  const wmCanvas = watermarkRef.value
  wmCanvas.height = canvasRef.value.height
  wmCanvas.width = canvasRef.value.width
  const wmCtx = wmCanvas.getContext('2d')!
  canvasWatermark(wmCtx, wmCanvas.width, wmCanvas.height)
}

async function renderPage() {
  if (!canvasRef.value || !pdfDoc) return
  const pdfPage = await pdfDoc.getPage(page.value)
  const viewport = pdfPage.getViewport({ scale: 1.5 })
  const canvas = canvasRef.value
  canvas.height = viewport.height
  canvas.width = viewport.width
  const ctx = canvas.getContext('2d')!
  await pdfPage.render({ canvasContext: ctx, viewport }).promise
  renderWatermark()

  // Also render to fullscreen canvas if visible
  if (fs.isFullscreen.value && fsCanvasRef.value) {
    const fsViewport = pdfPage.getViewport({ scale: 2.0 })
    const fsCanvas = fsCanvasRef.value
    fsCanvas.height = fsViewport.height
    fsCanvas.width = fsViewport.width
    const fsCtx = fsCanvas.getContext('2d')!
    await pdfPage.render({ canvasContext: fsCtx, viewport: fsViewport }).promise
  }
}

watch(page, () => { renderPage() })
watch(() => fs.isFullscreen.value, (v) => { if (v) renderPage() })
</script>
