<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <NuxtLink to="/user/profile" class="flex items-center gap-1 text-sm text-slate-500 hover:text-primary-600 mb-4 no-underline">
      <AppIcon name="ArrowLeft" :size="14" /> 返回个人中心
    </NuxtLink>

    <h1 class="text-xl font-semibold text-slate-900 mb-6">隐私设置</h1>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
    </div>

    <div v-else class="space-y-6">
      <!-- Display name -->
      <div class="bg-white border border-slate-200 rounded-lg p-6">
        <h3 class="text-base font-medium text-slate-800 mb-1">公开贡献显示名</h3>
        <p class="text-sm text-slate-500 mb-4">
          决定你的贡献在资料详情页和课程列表中的公开显示方式
        </p>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              v-model="displayMode"
              type="radio"
              value="anonymous"
              name="displayMode"
              class="w-4 h-4 text-primary-600"
            />
            <span class="text-sm text-slate-700">匿名用户</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              v-model="displayMode"
              type="radio"
              value="nickname"
              name="displayMode"
              class="w-4 h-4 text-primary-600"
            />
            <span class="text-sm text-slate-700">使用昵称</span>
          </label>
        </div>
        <div class="mt-3 bg-slate-50 rounded-md px-3 py-2 text-xs text-slate-500">
          资料详情页将显示为：<span class="font-medium text-slate-700">{{ previewName }}</span>
        </div>
        <button
          class="mt-4 h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer transition-colors duration-150"
          :disabled="saving"
          @click="savePrivacy"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
        <p v-if="saveMsg" class="mt-2 text-xs text-emerald-600">{{ saveMsg }}</p>
      </div>

      <!-- Account deactivation -->
      <div class="bg-white border border-red-200 rounded-lg p-6">
        <h3 class="text-base font-medium text-red-700 mb-1">注销账户</h3>
        <p class="text-sm text-slate-500 mb-4">
          注销后，你的个人信息将在 30 天内被删除，贡献资料将匿名化处理。此操作不可撤销。
        </p>
        <button
          v-if="!showDeactivateConfirm"
          class="h-9 px-4 rounded-md text-sm font-medium border border-red-200 text-red-600 hover:bg-red-50 cursor-pointer transition-colors duration-150"
          @click="showDeactivateConfirm = true"
        >
          注销账户
        </button>
        <div v-else class="bg-red-50 rounded-md p-4">
          <p class="text-sm text-red-700 font-medium mb-3">确认注销账户？此操作不可撤销。</p>
          <div class="flex gap-3">
            <button
              class="h-9 px-4 rounded-md text-sm bg-red-600 text-white hover:bg-red-700 cursor-pointer transition-colors duration-150"
              :disabled="deactivating"
              @click="handleDeactivate"
            >
              {{ deactivating ? '处理中...' : '确认注销' }}
            </button>
            <button
              class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors duration-150"
              @click="showDeactivateConfirm = false"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const auth = useAuthStore()
const displayMode = ref<'anonymous' | 'nickname'>('anonymous')
const loading = ref(true)
const saving = ref(false)
const deactivating = ref(false)
const saveMsg = ref('')
const showDeactivateConfirm = ref(false)

const previewName = computed(() =>
  displayMode.value === 'anonymous' ? '匿名贡献' : (auth.user?.nickname || '')
)

onMounted(async () => {
  const { getPrivacy } = useAuth()
  try {
    const resp = await getPrivacy()
    if (resp.code === 0 && resp.data) {
      displayMode.value = resp.data.public_display_name === '匿名用户' ? 'anonymous' : 'nickname'
    }
  } catch { /* noop */ }
  loading.value = false
})

async function savePrivacy() {
  saving.value = true
  saveMsg.value = ''
  const { updatePrivacy } = useAuth()
  try {
    const displayName = displayMode.value === 'anonymous' ? '匿名用户' : (auth.user?.nickname || '')
    await updatePrivacy(displayName)
    saveMsg.value = '设置已保存'
    setTimeout(() => { saveMsg.value = '' }, 3000)
  } catch { /* noop */ }
  saving.value = false
}

async function handleDeactivate() {
  deactivating.value = true
  const { deactivateAccount } = useAuth()
  try {
    await deactivateAccount()
    await auth.doLogout()
    navigateTo('/')
  } catch { /* noop */ }
  deactivating.value = false
}
</script>
