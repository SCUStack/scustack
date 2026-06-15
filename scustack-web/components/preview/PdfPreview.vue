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
        <a :href="downloadUrl" class="text-xs text-primary-600 hover:text-primary-700">下载 PDF</a>
      </div>
      <div class="relative border border-slate-200 rounded-lg overflow-hidden bg-slate-100">
        <canvas ref="canvasRef" class="w-full" />
        <canvas ref="watermarkRef" class="absolute inset-0 w-full h-full pointer-events-none" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ url: string; downloadUrl: string }>()

const canvasRef = ref<HTMLCanvasElement>()
const watermarkRef = ref<HTMLCanvasElement>()
const loading = ref(true)
const error = ref('')
const page = ref(1)
const totalPages = ref(0)
let pdfDoc: any = null

const { canvasWatermark } = useWatermark()

onMounted(async () => {
  try {
    const pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`
    const loadingTask = pdfjsLib.getDocument({ url: props.url })
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    await renderPage()
  } catch {
    error.value = 'PDF 预览加载失败'
  }
  loading.value = false
})

async function renderPage() {
  if (!canvasRef.value || !pdfDoc) return
  const pdfPage = await pdfDoc.getPage(page.value)
  const viewport = pdfPage.getViewport({ scale: 1.5 })
  const canvas = canvasRef.value
  canvas.height = viewport.height
  canvas.width = viewport.width
  const ctx = canvas.getContext('2d')!
  await pdfPage.render({ canvasContext: ctx, viewport }).promise

  if (watermarkRef.value) {
    const wmCanvas = watermarkRef.value
    wmCanvas.height = viewport.height
    wmCanvas.width = viewport.width
    const wmCtx = wmCanvas.getContext('2d')!
    canvasWatermark(wmCtx, viewport.width, viewport.height)
  }
}

watch(page, () => { renderPage() })
</script>
