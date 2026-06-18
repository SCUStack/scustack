<template>
  <div class="relative transition-all duration-300 ease-out" :class="variant === 'hero' ? 'w-full max-w-2xl mx-auto' : (isFocused ? 'w-80 sm:w-96' : 'w-48 sm:w-56')">
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

    <!-- Dropdown panel -->
    <div
      v-if="panelVisible"
      class="absolute top-full mt-1 left-0 right-0 bg-white border border-slate-200 rounded-lg shadow z-50 max-h-80 overflow-y-auto"
      @mousedown.prevent
    >
      <!-- Autocomplete suggestions (when query has text) -->
      <template v-if="query && suggestions.length > 0">
        <div v-for="(item, idx) in suggestions" :key="item.id || idx"
             :class="['px-3 py-2 flex items-center gap-2 text-sm cursor-pointer', idx === highlightIdx ? 'bg-primary-50' : 'hover:bg-slate-50']"
             @mousedown.prevent="selectSuggestion(item)">
          <AppIcon :name="item.type === 'course' ? 'BookOpen' : 'FileText'" :size="16" class="text-slate-400 shrink-0" />
          <div>
            <p class="text-slate-700">{{ item.label }}</p>
            <p class="text-xs text-slate-400">{{ item.type === 'course' ? '课程' : '资料' }}{{ item.sub ? ` · ${item.sub}` : '' }}</p>
          </div>
        </div>
      </template>

      <!-- History + hot searches (when query is empty) -->
      <template v-if="!query">
        <!-- Search history -->
        <div v-if="searchHistory.length > 0" class="p-1">
          <div class="flex items-center justify-between px-2 py-1.5">
            <span class="text-xs font-medium text-slate-500">搜索历史</span>
            <button class="text-xs text-slate-400 hover:text-slate-600 cursor-pointer border-none bg-transparent p-0" @click.stop="clearHistory">清除全部</button>
          </div>
          <div
            v-for="(term, idx) in searchHistory"
            :key="'h-' + idx"
            class="flex items-center justify-between px-3 py-1.5 rounded hover:bg-slate-50 cursor-pointer group"
            :class="idx === highlightIdx ? 'bg-primary-50' : ''"
            @mousedown.prevent="selectHistory(term)"
          >
            <div class="flex items-center gap-2">
              <AppIcon name="Clock" :size="14" class="text-slate-300" />
              <span class="text-sm text-slate-700 truncate max-w-[200px]">{{ term }}</span>
            </div>
            <button class="text-slate-300 hover:text-slate-500 cursor-pointer border-none bg-transparent p-0 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop="removeHistory(idx)">
              <AppIcon name="X" :size="12" />
            </button>
          </div>
        </div>

        <!-- Hot searches -->
        <div v-if="hotKeywords.length > 0" class="p-1" :class="searchHistory.length > 0 ? 'border-t border-slate-100' : ''">
          <div class="px-2 py-1.5">
            <span class="text-xs font-medium text-slate-500">热门搜索</span>
          </div>
          <div
            v-for="(kw, idx) in hotKeywords"
            :key="'hot-' + idx"
            class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-slate-50 cursor-pointer"
            :class="(searchHistory.length + idx) === highlightIdx ? 'bg-primary-50' : ''"
            @mousedown.prevent="selectHistory(kw.text)"
          >
            <AppIcon name="TrendingUp" :size="14" class="text-amber-400" />
            <span class="text-sm text-slate-700 truncate max-w-[200px]">{{ kw.text }}</span>
            <span v-if="kw.count" class="text-[10px] text-slate-400 ml-auto">{{ kw.count }}</span>
          </div>
        </div>

        <!-- Empty state when no history and hot fails -->
        <div v-if="searchHistory.length === 0 && hotKeywords.length === 0 && !hotLoading" class="px-3 py-4 text-center">
          <p class="text-xs text-slate-400">输入关键词搜索课程和资料</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

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
const isFocused = ref(false)
let abortController: AbortController | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const searchHistory = ref<string[]>([])
const hotKeywords = ref<{ text: string; count: number }[]>([])
const hotLoading = ref(false)

const panelVisible = computed(() => {
  if (!isFocused.value) return false
  if (query.value) return showSuggestions.value && suggestions.value.length > 0
  return true // Show history + hot when focused and empty
})

function loadHistory() {
  try {
    const raw = localStorage.getItem('scustack_search_history')
    if (raw) searchHistory.value = JSON.parse(raw)
  } catch { searchHistory.value = [] }
}

function saveToHistory(term: string) {
  const t = term.trim()
  if (!t) return
  searchHistory.value = [t, ...searchHistory.value.filter(h => h !== t)].slice(0, 20)
  try { localStorage.setItem('scustack_search_history', JSON.stringify(searchHistory.value)) } catch { /* noop */ }
}

function removeHistory(idx: number) {
  searchHistory.value.splice(idx, 1)
  try { localStorage.setItem('scustack_search_history', JSON.stringify(searchHistory.value)) } catch { /* noop */ }
}

function clearHistory() {
  searchHistory.value = []
  try { localStorage.removeItem('scustack_search_history') } catch { /* noop */ }
}

async function fetchHotSearches() {
  hotLoading.value = true
  try {
    const resp = await $fetch<{ code: number; data: { keywords: { text: string; count: number }[] } }>(
      `${apiBase}/api/v1/search/hot`
    )
    if (resp.code === 0) hotKeywords.value = resp.data.keywords
  } catch { /* noop */ }
  hotLoading.value = false
}

const inputClass = computed(() =>
  props.variant === 'hero'
    ? 'w-full h-14 pl-10 pr-10 border border-slate-200 rounded-lg text-base text-slate-800 bg-white outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 shadow-sm transition-shadow duration-200'
    : 'w-full h-10 pl-9 pr-8 border border-slate-200 rounded-md text-sm text-slate-800 bg-white outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200'
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
  if (highlightIdx.value >= 0) {
    const allItems = query.value ? suggestions.value : [...searchHistory.value.map(t => ({ type: 'history', label: t, to: `/search?q=${encodeURIComponent(t)}` })), ...hotKeywords.value.map(k => ({ type: 'hot', label: k.text, to: `/search?q=${encodeURIComponent(k.text)}` }))]
    if (highlightIdx.value < allItems.length) {
      if (query.value) selectSuggestion(suggestions.value[highlightIdx.value])
      else {
        const item = allItems[highlightIdx.value]
        selectHistory(item.label)
      }
      return
    }
  }
  closeSuggestions()
  if (query.value.trim()) {
    saveToHistory(query.value.trim())
    navigateTo(`/search?q=${encodeURIComponent(query.value.trim())}`)
  }
}

function onArrowDown() {
  const items = query.value ? suggestions.value : [...searchHistory.value, ...hotKeywords.value.map(k => k.text)]
  if (items.length === 0) return
  highlightIdx.value = (highlightIdx.value + 1) % items.length
}

function onArrowUp() {
  const items = query.value ? suggestions.value : [...searchHistory.value, ...hotKeywords.value.map(k => k.text)]
  if (items.length === 0) return
  highlightIdx.value = highlightIdx.value > 0 ? highlightIdx.value - 1 : items.length - 1
}

function selectSuggestion(item: { type: string; label: string; to: string }) {
  query.value = item.label
  saveToHistory(item.label)
  closeSuggestions()
  if (item.to.startsWith('/')) navigateTo(item.to)
  else navigateTo(`/search?q=${encodeURIComponent(item.label)}`)
}

function selectHistory(term: string) {
  query.value = term
  saveToHistory(term)
  closeSuggestions()
  navigateTo(`/search?q=${encodeURIComponent(term)}`)
}

function closeSuggestions() {
  showSuggestions.value = false
  highlightIdx.value = -1
  isFocused.value = false
}

function onFocus() {
  isFocused.value = true
  if (query.value && suggestions.value.length > 0) showSuggestions.value = true
}

function onBlur() {
  setTimeout(() => closeSuggestions(), 150)
}

function clear() {
  query.value = ''
  suggestions.value = []
  showSuggestions.value = false
  isFocused.value = false
  inputRef.value?.focus()
}

onMounted(() => {
  loadHistory()
  fetchHotSearches()
})
</script>
