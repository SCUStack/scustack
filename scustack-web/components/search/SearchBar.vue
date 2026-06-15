<template>
  <div class="relative" :class="variant === 'hero' ? 'w-full max-w-2xl mx-auto' : 'w-64'">
    <div class="relative">
      <AppIcon name="Search" :size="variant === 'hero' ? 20 : 16"
               class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      <input
        ref="inputRef"
        v-model="query"
        :class="inputClass"
        :placeholder="placeholder"
        @input="onInput"
        @keydown.escape="closeSuggestions"
        @keydown.enter.prevent="onEnter"
        @keydown.down.prevent="onArrowDown"
        @keydown.up.prevent="onArrowUp"
        @focus="onFocus"
        @blur="onBlur"
      />
      <button v-if="query" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer" @click="clear">
        <AppIcon name="X" :size="14" />
      </button>
    </div>

    <div
      v-if="showSuggestions && suggestions.length > 0"
      class="absolute top-full mt-1 left-0 right-0 bg-white border border-slate-200 rounded-lg shadow z-50 max-h-80 overflow-y-auto"
    >
      <div v-for="(item, idx) in suggestions" :key="item.id || idx"
           :class="['px-3 py-2 flex items-center gap-2 text-sm cursor-pointer', idx === highlightIdx ? 'bg-primary-50' : 'hover:bg-slate-50']"
           @mousedown.prevent="selectSuggestion(item)">
        <AppIcon :name="item.type === 'course' ? 'BookOpen' : 'FileText'" :size="16" class="text-slate-400 shrink-0" />
        <div>
          <p class="text-slate-700">{{ item.label }}</p>
          <p class="text-xs text-slate-400">{{ item.type === 'course' ? '课程' : '资料' }}{{ item.sub ? ` · ${item.sub}` : '' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  variant?: 'nav' | 'hero'
  placeholder?: string
}>(), {
  variant: 'nav',
  placeholder: '搜索课程、资料...',
})

const emit = defineEmits<{ search: [query: string] }>()

const { apiBase } = useRuntimeConfig().public
const query = ref('')
const suggestions = ref<{ id?: string; type: string; label: string; sub?: string; to: string }[]>([])
const showSuggestions = ref(false)
const highlightIdx = ref(-1)
const inputRef = ref<HTMLInputElement>()
let abortController: AbortController | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const inputClass = computed(() =>
  props.variant === 'hero'
    ? 'w-full h-14 pl-10 pr-10 border border-slate-200 rounded-lg text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 shadow-sm transition-shadow duration-200'
    : 'w-full h-10 pl-9 pr-8 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200'
)

function onInput() {
  highlightIdx.value = -1
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchSuggestions, 300)

  if (query.value.length > 0) {
    emit('search', query.value)
  }
}

async function fetchSuggestions() {
  if (abortController) abortController.abort()
  if (query.value.length < 1) { suggestions.value = []; showSuggestions.value = false; return }

  abortController = new AbortController()
  try {
    const resp = await $fetch<{ code: number; data: { courses: string[]; materials: string[] } }>(
      `${apiBase}/api/v1/search/suggest?q=${encodeURIComponent(query.value)}`,
      { signal: abortController.signal },
    )
    if (resp.code === 0) {
      const items: typeof suggestions.value = []
      for (const c of resp.data.courses) {
        items.push({ type: 'course', label: c, to: `/search?q=${encodeURIComponent(c)}` })
      }
      for (const m of resp.data.materials) {
        items.push({ type: 'material', label: m, to: `/search?q=${encodeURIComponent(m)}` })
      }
      suggestions.value = items
      showSuggestions.value = items.length > 0
    }
  } catch {
    // aborted or network error, ignore
  }
}

function onEnter() {
  if (highlightIdx.value >= 0 && highlightIdx.value < suggestions.value.length) {
    selectSuggestion(suggestions.value[highlightIdx.value])
    return
  }
  closeSuggestions()
  if (query.value.trim()) navigateTo(`/search?q=${encodeURIComponent(query.value.trim())}`)
}

function onArrowDown() {
  if (suggestions.value.length === 0) return
  highlightIdx.value = (highlightIdx.value + 1) % suggestions.value.length
}

function onArrowUp() {
  if (suggestions.value.length === 0) return
  highlightIdx.value = highlightIdx.value > 0 ? highlightIdx.value - 1 : suggestions.value.length - 1
}

function selectSuggestion(item: { type: string; label: string; to: string }) {
  query.value = item.label
  closeSuggestions()
  if (item.to.startsWith('/')) navigateTo(item.to)
  else navigateTo(`/search?q=${encodeURIComponent(item.label)}`)
}

function closeSuggestions() {
  showSuggestions.value = false
  highlightIdx.value = -1
}

function onFocus() {
  if (suggestions.value.length > 0) showSuggestions.value = true
}

function onBlur() {
  setTimeout(() => closeSuggestions(), 150)
}

function clear() {
  query.value = ''
  suggestions.value = []
  showSuggestions.value = false
  inputRef.value?.focus()
}
</script>
