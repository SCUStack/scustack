<template>
  <Teleport to="body">
    <Transition name="share-dialog">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[80] flex items-end justify-center bg-slate-900/45 p-0 sm:items-center sm:p-4"
        @click.self="close"
      >
        <section
          ref="dialogRef"
          role="dialog"
          aria-modal="true"
          aria-labelledby="share-dialog-title"
          class="w-full rounded-t-lg bg-white shadow-xl sm:max-w-md sm:rounded-lg"
          tabindex="-1"
        >
          <header class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <div class="flex min-w-0 items-center gap-2.5">
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary-50 text-primary-700">
                <AppIcon name="Share2" :size="18" />
              </span>
              <div class="min-w-0">
                <h2 id="share-dialog-title" class="text-base font-semibold text-slate-900">分享资料</h2>
                <p class="truncate text-xs text-slate-500">{{ title }}</p>
              </div>
            </div>
            <button
              type="button"
              aria-label="关闭分享弹窗"
              title="关闭"
              class="flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-md text-slate-400 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-700"
              @click="close"
            >
              <AppIcon name="X" :size="18" />
            </button>
          </header>

          <div class="space-y-4 px-5 py-5">
            <div>
              <p class="mb-1.5 text-xs font-medium text-slate-600">分享内容</p>
              <div class="min-h-[120px] whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm leading-6 text-slate-700">
                {{ shareText }}
              </div>
            </div>

            <button
              type="button"
              class="flex min-h-[44px] w-full cursor-pointer items-center justify-center gap-2 rounded-md bg-primary-700 px-4 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-300 focus-visible:ring-offset-2"
              @click="copyShareContent"
            >
              <AppIcon :name="copied ? 'Check' : 'Copy'" :size="16" />
              {{ copied ? '分享内容已复制' : '复制分享内容' }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  materialId: string
  title: string
  description?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const dialogRef = ref<HTMLElement | null>(null)
const copied = ref(false)
const toast = useToast()
let copiedTimer: ReturnType<typeof setTimeout> | null = null

const shareUrl = computed(() => {
  const path = `/material/${props.materialId}`
  return typeof window === 'undefined' ? path : new URL(path, window.location.origin).toString()
})

const shareDescription = computed(() => {
  const description = props.description?.replace(/\s+/g, ' ').trim()
  if (!description) return '四川大学课程学习资料，欢迎查看与分享。'
  return description.length > 120 ? `${description.slice(0, 120)}...` : description
})

const shareText = computed(() => `川流课栈｜${props.title}\n${shareDescription.value}\n查看资料：${shareUrl.value}`)

watch(() => props.modelValue, async (open) => {
  copied.value = false
  if (open) {
    await nextTick()
    dialogRef.value?.focus()
  }
})

function close() {
  emit('update:modelValue', false)
}

function onKeydown(event: KeyboardEvent) {
  if (props.modelValue && event.key === 'Escape') close()
}

async function copyShareContent() {
  try {
    await navigator.clipboard.writeText(shareText.value)
    copied.value = true
    toast.success('分享内容已复制')
    if (copiedTimer) clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => { copied.value = false }, 2000)
  } catch {
    toast.error('复制失败，请手动复制分享内容')
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (copiedTimer) clearTimeout(copiedTimer)
})
</script>

<style scoped>
.share-dialog-enter-active,
.share-dialog-leave-active { transition: opacity 0.2s ease; }
.share-dialog-enter-active > section,
.share-dialog-leave-active > section { transition: transform 0.2s ease, opacity 0.2s ease; }
.share-dialog-enter-from,
.share-dialog-leave-to { opacity: 0; }
.share-dialog-enter-from > section,
.share-dialog-leave-to > section { opacity: 0; transform: translateY(16px); }

@media (prefers-reduced-motion: reduce) {
  .share-dialog-enter-active,
  .share-dialog-leave-active,
  .share-dialog-enter-active > section,
  .share-dialog-leave-active > section { transition: none; }
}
</style>
