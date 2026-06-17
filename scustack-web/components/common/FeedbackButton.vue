<template>
  <div>
    <button
      class="fixed bottom-16 lg:bottom-6 right-6 z-40 w-11 h-11 rounded-full bg-primary-700 text-white shadow-lg hover:bg-primary-800 hover:shadow-xl cursor-pointer border-none flex items-center justify-center transition-all duration-200"
      aria-label="反馈"
      title="帮助我们变得更好"
      @click="showModal = true"
    >
      <AppIcon name="MessageSquare" :size="20" />
    </button>

    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4" role="dialog" aria-modal="true" aria-label="反馈">
          <h3 class="text-base font-medium text-slate-900 mb-4">帮助我们变得更好</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">反馈类型</label>
              <select v-model="type" class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500">
                <option value="bug">Bug 反馈</option>
                <option value="feature">功能建议</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">描述</label>
              <textarea
                v-model="content"
                maxlength="2000"
                rows="4"
                class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm resize-none outline-none focus:border-primary-500"
                placeholder="请描述您遇到的问题或建议..."
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">邮箱（选填，用于回复）</label>
              <input
                v-model="email"
                type="email"
                maxlength="200"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500"
                placeholder="your@email.com"
              />
            </div>
            <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>
            <div class="flex justify-end gap-3 pt-1">
              <button
                class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer border-none bg-transparent transition-colors duration-150"
                @click="showModal = false"
              >
                取消
              </button>
              <button
                class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer border-none transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!content.trim() || submitting"
                @click="submit"
              >
                {{ submitting ? '提交中...' : '提交反馈' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public
const toast = useToast()

const showModal = ref(false)
const type = ref('bug')
const content = ref('')
const email = ref('')
const submitting = ref(false)
const errorMsg = ref('')

async function submit() {
  if (!content.value.trim()) return
  submitting.value = true
  errorMsg.value = ''
  try {
    const resp = await $fetch<{ code: number; message: string }>(`${apiBase}/api/v1/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: type.value,
        content: content.value.trim(),
        email: email.value.trim() || undefined,
      }),
      credentials: 'include',
    })
    if (resp.code === 0) {
      showModal.value = false
      type.value = 'bug'
      content.value = ''
      email.value = ''
      toast.success('感谢反馈！')
    } else {
      errorMsg.value = resp.message || '提交失败'
    }
  } catch {
    errorMsg.value = '提交失败，请稍后重试'
  }
  submitting.value = false
}
</script>
