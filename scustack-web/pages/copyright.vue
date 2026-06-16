<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
    <div class="mb-6">
      <h1 class="text-xl font-semibold text-slate-900 mb-2">版权投诉</h1>
      <p class="text-sm text-slate-500">
        如果您认为本站内容侵犯了您的著作权，请填写以下表单。我们将在 48 小时内处理有效投诉。
      </p>
    </div>

    <div v-if="submitted" class="text-center py-12">
      <AppIcon name="CheckCircle" :size="48" class="text-emerald-500 mx-auto mb-4" />
      <h2 class="text-lg font-medium text-slate-800 mb-2">投诉已提交</h2>
      <p class="text-sm text-slate-500 mb-1">工单编号：<span class="font-mono font-medium text-slate-700">{{ ticketNumber }}</span></p>
      <p class="text-xs text-slate-400">我们将在 48 小时内处理并邮件通知您</p>
      <NuxtLink to="/" class="inline-flex items-center gap-1 mt-6 text-sm text-primary-600 hover:text-primary-700 no-underline">
        <AppIcon name="ArrowLeft" :size="14" /> 返回首页
      </NuxtLink>
    </div>

    <form v-else @submit.prevent="submit" class="space-y-5">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">您的姓名 / 机构名称 *</label>
        <input v-model="form.complainant_name" maxlength="100" required
               class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="个人姓名或版权方机构名称" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">联系邮箱 *</label>
        <input v-model="form.contact_email" type="email" maxlength="200" required
               class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="用于接收处理结果通知" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">联系电话</label>
        <input v-model="form.contact_phone" maxlength="30"
               class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="选填" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">侵权资料链接 *</label>
        <input v-model="form.infringing_url" maxlength="2000" required
               class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
               placeholder="https://scustack.com/material/..." />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">侵权说明</label>
        <textarea v-model="form.infringing_description" rows="3" maxlength="2000"
                  class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 resize-none"
                  placeholder="请简要说明侵权内容及您的权利证明" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">声明 *</label>
        <textarea v-model="form.statement" rows="3" maxlength="5000" required
                  class="w-full px-3 py-2 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 resize-none"
                  :placeholder="statementPlaceholder" />
        <p class="text-xs text-slate-400 mt-1">{{ form.statement.length }}/5000</p>
      </div>

      <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

      <div class="flex gap-3 pt-4 border-t border-slate-200">
        <button type="submit" :disabled="!canSubmit || submitting"
                class="px-6 h-10 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer transition-colors duration-150">
          {{ submitting ? '提交中...' : '提交投诉' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: false })

const { apiBase } = useRuntimeConfig().public

const submitted = ref(false)
const ticketNumber = ref('')
const submitting = ref(false)
const errorMsg = ref('')

const statementPlaceholder = `本人声明：
1. 本人为上述资料的著作权人或被授权代理人
2. 上述资料未经授权被发布在川流课栈
3. 本人承诺以上信息真实准确，如有虚假愿承担法律责任

签名：
日期：`

const form = reactive({
  complainant_name: '',
  contact_email: '',
  contact_phone: '',
  infringing_url: '',
  infringing_description: '',
  statement: '',
})

const canSubmit = computed(() => {
  return form.complainant_name && form.contact_email && form.infringing_url && form.statement.length >= 10
})

async function submit() {
  errorMsg.value = ''
  submitting.value = true
  try {
    const resp = await $fetch<{ code: number; data?: { ticket_number: string }; message: string }>(
      `${apiBase}/api/v1/copyright/complaint`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form }),
      },
    )
    if (resp.code === 0) {
      ticketNumber.value = resp.data?.ticket_number || ''
      submitted.value = true
    } else {
      errorMsg.value = resp.message
    }
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '提交失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>
