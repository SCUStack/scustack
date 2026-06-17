<template>
  <div class="border-t border-slate-200 pt-8 mt-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <h2 class="text-lg font-semibold text-slate-800 mb-4">评论 ({{ total }})</h2>

    <!-- Input -->
    <div v-if="auth.isLoggedIn" class="flex gap-3 mb-6">
      <textarea
        v-model="content"
        maxlength="2000"
        rows="2"
        class="flex-1 px-3 py-2 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 resize-none"
        placeholder="写评论..."
        @keydown.enter.ctrl="submitComment()"
      />
      <button
        :disabled="!content.trim() || submitting"
        class="shrink-0 self-end h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 cursor-pointer transition-colors"
        @click="submitComment()"
      >{{ submitting ? '...' : '发布' }}</button>
    </div>
    <button v-else class="mb-6 inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors" @click="auth.openLogin">
      <AppIcon name="LogIn" :size="14" /> 登录后评论
    </button>

    <!-- List -->
    <div v-if="comments.length" class="space-y-1">
      <div v-for="c in comments" :key="c.id" class="py-3">
        <div class="flex items-start gap-2.5">
          <div class="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
            <AppIcon name="User" :size="14" class="text-primary-500" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-xs font-medium text-slate-700">{{ c.nickname }}</span>
              <span class="text-[10px] text-slate-400">{{ timeAgo(c.created_at) }}</span>
            </div>
            <p class="text-sm text-slate-700 leading-relaxed">{{ c.content }}</p>
            <div class="flex items-center gap-3 mt-1.5">
              <button class="text-[11px] text-slate-400 hover:text-primary-600 cursor-pointer transition-colors border-none bg-transparent p-0" @click="startReply(c.id)">回复</button>
              <button
                v-if="c.user_id === currentUserId || isAdmin"
                class="text-[11px] text-slate-400 hover:text-red-500 cursor-pointer transition-colors border-none bg-transparent p-0"
                @click="deleteComment(c.id)"
              >删除</button>
            </div>

            <!-- Reply form -->
            <div v-if="replyingTo === c.id" class="mt-2 flex gap-2">
              <input v-model="replyContent" maxlength="500" class="flex-1 h-8 px-2 border border-slate-200 rounded text-xs outline-none focus:border-primary-500" placeholder="回复 {{ c.nickname }}..." @keydown.enter="submitReply(c.id)" />
              <button class="h-8 px-3 rounded text-xs font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer transition-colors" @click="submitReply(c.id)">回复</button>
              <button class="h-8 px-2 rounded text-xs text-slate-400 hover:text-slate-600 cursor-pointer transition-colors border-none bg-transparent" @click="replyingTo = ''">取消</button>
            </div>

            <!-- Replies -->
            <div v-if="c.replies?.length" class="mt-2 pl-4 border-l-2 border-slate-100 space-y-0.5">
              <div v-for="r in c.replies" :key="r.id" class="py-1.5">
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="text-xs font-medium text-slate-600">{{ r.nickname }}</span>
                  <span class="text-[10px] text-slate-400">{{ timeAgo(r.created_at) }}</span>
                </div>
                <p class="text-sm text-slate-600">{{ r.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="text-center py-8 text-sm text-slate-400">暂无评论</div>
    <div v-if="loading" class="py-4"><SkeletonList :count="3" /></div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ materialId: string }>()

const auth = useAuthStore()
const toast = useToast()
const { apiBase } = useRuntimeConfig().public

const comments = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const content = ref('')
const submitting = ref(false)
const replyingTo = ref('')
const replyContent = ref('')
const currentUserId = ref('')
const isAdmin = ref(false)

async function fetchComments() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: any[]; total: number }>(
      `${apiBase}/api/v1/materials/${props.materialId}/comments`
    )
    if (resp.code === 0) { comments.value = resp.data; total.value = resp.total }
  } catch { /* noop */ }
  loading.value = false
}

async function submitComment() {
  if (!content.value.trim()) return
  submitting.value = true
  try {
    const resp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/materials/${props.materialId}/comments`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.value.trim() }),
    })
    if (resp.code === 0) { content.value = ''; await fetchComments() }
    else toast.error(resp.message || '评论失败')
  } catch { toast.error('评论失败') }
  submitting.value = false
}

function startReply(id: string) { replyingTo.value = id; replyContent.value = '' }

async function submitReply(parentId: string) {
  if (!replyContent.value.trim()) return
  try {
    const resp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/materials/${props.materialId}/comments`, {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: replyContent.value.trim(), parent_id: parentId }),
    })
    if (resp.code === 0) { replyContent.value = ''; replyingTo.value = ''; await fetchComments() }
    else toast.error('回复失败')
  } catch { toast.error('回复失败') }
}

async function deleteComment(id: string) {
  try {
    await $fetch(`${apiBase}/api/v1/comments/${id}`, { method: 'DELETE', credentials: 'include' })
    await fetchComments()
  } catch { /* noop */ }
}

function timeAgo(d: string): string {
  const diff = Date.now() - new Date(d).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

onMounted(async () => {
  if (auth.isLoggedIn) {
    try {
      const me = await $fetch<{ code: number; data: { id: string; role: string } }>(
        `${apiBase}/api/v1/auth/me`, { credentials: 'include' }
      )
      if (me.code === 0) { currentUserId.value = me.data.id; isAdmin.value = me.data.role === 'admin' }
    } catch { /* noop */ }
  }
  fetchComments()
})
</script>
