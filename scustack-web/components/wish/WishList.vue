<template>
  <div class="border-t border-slate-200 pt-8 mt-8">
    <div class="flex items-center gap-2 mb-4">
      <AppIcon name="Heart" :size="20" class="text-rose-500" />
      <h2 class="text-lg font-semibold text-slate-900">心愿单</h2>
      <span class="text-sm text-slate-400">{{ total }} 条心愿</span>
    </div>

    <!-- Create wish -->
    <div v-if="auth.isLoggedIn" class="mb-5 p-4 bg-slate-50 rounded-lg border border-slate-200">
      <div class="flex gap-3">
        <input
          v-model="newTitle"
          maxlength="200"
          class="flex-1 h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
          placeholder="求一份..."
          @keydown.enter="createWish"
        />
        <select v-model="newCategory" class="h-10 px-3 border border-slate-200 rounded-md text-sm outline-none">
          <option value="">选择分类</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <button
          :disabled="!newTitle.trim() || creating"
          class="shrink-0 h-10 px-5 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150"
          @click="createWish"
        >
          {{ creating ? '发布中...' : '发布心愿' }}
        </button>
      </div>
      <p v-if="createError" class="text-xs text-red-500 mt-1.5">{{ createError }}</p>
    </div>
    <button
      v-else
      class="mb-5 inline-flex items-center gap-1.5 h-10 px-4 rounded-md text-sm font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors duration-150"
      @click="auth.openLogin"
    >
      <AppIcon name="LogIn" :size="14" /> 登录后发布心愿
    </button>

    <!-- Wish items -->
    <div v-if="wishes.length" class="space-y-3">
      <div
        v-for="w in wishes"
        :key="w.id"
        class="flex items-start gap-3 p-3.5 rounded-lg border border-slate-100 hover:border-slate-200 transition-colors duration-150"
      >
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-slate-800">{{ w.title }}</p>
          <p v-if="w.description" class="text-xs text-slate-500 mt-0.5 line-clamp-2">{{ w.description }}</p>
          <div class="flex items-center gap-2 mt-1.5">
            <span v-if="w.category" class="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{{ w.category }}</span>
            <span class="text-xs text-slate-400">{{ timeAgo(w.created_at) }}</span>
          </div>
        </div>
        <button
          class="shrink-0 inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-sm cursor-pointer transition-colors duration-150"
          :class="w.has_voted ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'border border-slate-200 text-slate-500 hover:bg-slate-50'"
          @click="toggleVote(w)"
        >
          <AppIcon :name="w.has_voted ? 'Heart' : 'Heart'" :size="14" :class="w.has_voted ? 'fill-rose-500' : ''" />
          {{ w.vote_count }}
        </button>
      </div>
    </div>
    <div v-else-if="!loading" class="text-center py-6 text-sm text-slate-400">
      暂无心愿，成为第一个许愿的人
    </div>

    <div v-if="loading" class="py-4">
      <SkeletonList :count="3" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { materialCategories } from '~/data/business'

const props = defineProps<{ courseId: string }>()

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months} 个月前`
  return `${Math.floor(months / 12)} 年前`
}

const auth = useAuthStore()
const { apiBase } = useRuntimeConfig().public

const wishes = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const newTitle = ref('')
const newCategory = ref('')
const creating = ref(false)
const createError = ref('')

const categories = [...materialCategories]

async function fetchWishes() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[]; total: number }>(
      `${apiBase}/api/v1/wishes?course_id=${props.courseId}&sort=votes&page_size=50`
    )
    if (resp.code === 0) {
      wishes.value = resp.data || []
      total.value = resp.total || 0
    }
  } catch { /* noop */ } finally {
    loading.value = false
  }
}

async function createWish() {
  if (!newTitle.value.trim()) return
  createError.value = ''
  creating.value = true
  try {
    const resp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/wishes`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        course_id: props.courseId,
        title: newTitle.value.trim(),
        category: newCategory.value || undefined,
      }),
    })
    if (resp.code === 0) {
      newTitle.value = ''
      newCategory.value = ''
      await fetchWishes()
    } else {
      createError.value = resp.message
    }
  } catch {
    createError.value = '发布失败，请稍后重试'
  } finally {
    creating.value = false
  }
}

async function toggleVote(w: any) {
  if (!auth.isLoggedIn) {
    auth.openLogin()
    return
  }
  try {
    const resp = await $fetch<{ code: number; data: { action: string; vote_count: number } }>(`${apiBase}/api/v1/wishes/${w.id}/vote`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
    if (resp.code === 0) {
      w.has_voted = resp.data.action === 'voted'
      w.vote_count = resp.data.vote_count
    }
  } catch { /* noop */ }
}

onMounted(() => {
  fetchWishes()
})

watch(() => props.courseId, () => {
  fetchWishes()
})
</script>
