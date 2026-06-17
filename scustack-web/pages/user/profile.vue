<template>
  <div>
    <!-- Desktop -->
    <div class="hidden lg:block">
      <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '个人中心' }]" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 class="text-2xl font-semibold text-slate-900 mb-6">个人中心</h1>

      <div v-if="auth.user" class="space-y-6">
      <!-- Profile card -->
      <div class="bg-white border border-slate-200 rounded-lg p-6">
        <div class="flex items-start gap-4 mb-6">
          <div class="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
            <AppIcon name="User" :size="28" class="text-primary-600" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-medium text-slate-900">{{ auth.user.nickname }}</h2>
            <p class="text-sm text-slate-500 mt-0.5">
              {{ roleLabel }} · 信任分 {{ auth.user.trustScore }}
            </p>
            <p class="text-xs text-slate-400 mt-0.5">
              注册于 {{ formatDate(auth.user.id) }}
            </p>
          </div>
          <button
            class="text-sm text-primary-600 hover:text-primary-700 font-medium cursor-pointer"
            @click="showEdit = true"
          >
            编辑资料
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <NuxtLink
            to="/user/contributions"
            class="border border-slate-200 rounded-md p-3 hover:bg-slate-50 no-underline transition-colors duration-150"
          >
            <AppIcon name="Upload" :size="18" class="text-primary-500 mb-1" />
            <p class="text-sm font-medium text-slate-700">我的贡献</p>
            <p class="text-xs text-slate-400 mt-0.5">查看上传的资料</p>
          </NuxtLink>
          <NuxtLink
            to="/user/bookmarks"
            class="border border-slate-200 rounded-md p-3 hover:bg-slate-50 no-underline transition-colors duration-150"
          >
            <AppIcon name="Bookmark" :size="18" class="text-primary-500 mb-1" />
            <p class="text-sm font-medium text-slate-700">收藏与关注</p>
            <p class="text-xs text-slate-400 mt-0.5">管理收藏的资料和课程</p>
          </NuxtLink>
          <NuxtLink
            to="/user/privacy"
            class="border border-slate-200 rounded-md p-3 hover:bg-slate-50 no-underline transition-colors duration-150"
          >
            <AppIcon name="Shield" :size="18" class="text-primary-500 mb-1" />
            <p class="text-sm font-medium text-slate-700">隐私设置</p>
            <p class="text-xs text-slate-400 mt-0.5">管理公开显示名和账户</p>
          </NuxtLink>
        </div>
      </div>

      <!-- Badge wall -->
      <BadgeWall />

      <!-- Recent browsing -->
      <div class="bg-white border border-slate-200 rounded-lg p-6">
        <h3 class="text-base font-medium text-slate-800 mb-4">最近浏览</h3>
        <div v-if="recentItems.length > 0" class="divide-y divide-slate-100">
          <div
            v-for="item in recentItems"
            :key="item.id"
            class="flex items-center gap-3 py-2.5"
          >
            <AppIcon :name="item.type === 'material' ? 'FileText' : 'BookOpen'" :size="16" class="text-slate-400 shrink-0" />
            <NuxtLink :to="item.url" class="flex-1 text-sm text-primary-600 hover:text-primary-700 truncate no-underline">
              {{ item.title }}
            </NuxtLink>
            <span class="text-xs text-slate-400 shrink-0">{{ item.time }}</span>
          </div>
        </div>
        <EmptyState v-else icon="Clock" title="暂无浏览记录" />
      </div>
    </div>

    <!-- Logged-out state -->
    <div v-else class="text-center py-16 px-4">
      <div class="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-6">
        <AppIcon name="User" :size="40" class="text-primary-300" />
      </div>
      <h2 class="text-lg font-semibold text-slate-800 mb-2">登录以查看个人中心</h2>
      <p class="text-sm text-slate-500 mb-6">登录后可查看贡献、收藏和浏览记录</p>
      <button
        class="inline-flex items-center gap-2 h-10 px-6 rounded-lg text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer transition-colors"
        @click="auth.openLogin()"
      >
        <AppIcon name="LogIn" :size="16" /> 登录 / 注册
      </button>
    </div>

    <!-- Edit modal -->
    <div v-if="showEdit" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showEdit = false">
      <div class="bg-white rounded-lg p-6 w-full max-w-sm mx-4">
        <h3 class="text-base font-medium text-slate-900 mb-4">编辑资料</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">昵称</label>
            <input
              v-model="editForm.nickname"
              maxlength="64"
              class="w-full h-10 px-3 rounded-md border border-slate-200 text-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
            />
          </div>
          <div class="flex justify-end gap-3">
            <button
              class="h-9 px-4 rounded-md text-sm text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors duration-150"
              @click="showEdit = false"
            >
              取消
            </button>
            <button
              class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer transition-colors duration-150"
              :disabled="saving"
              @click="handleSave"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
    </div>

    <!-- Mobile -->
    <div class="lg:hidden px-4 pt-4 pb-4">
      <h1 class="text-lg font-semibold text-slate-900 mb-4">个人中心</h1>

      <div v-if="auth.user" class="space-y-4">
        <div class="bg-white border border-slate-200 rounded-xl p-4">
          <div class="flex items-start gap-3 mb-4">
            <div class="w-14 h-14 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
              <AppIcon name="User" :size="24" class="text-primary-600" />
            </div>
            <div class="flex-1 min-w-0">
              <h2 class="text-base font-medium text-slate-900">{{ auth.user.nickname }}</h2>
              <p class="text-xs text-slate-500 mt-0.5">{{ roleLabel }} · 信任分 {{ auth.user.trustScore }}</p>
            </div>
            <button class="text-xs text-primary-600 hover:text-primary-700 font-medium cursor-pointer" @click="showEdit = true">编辑</button>
          </div>
          <div class="grid grid-cols-1 gap-2">
            <NuxtLink to="/user/contributions" class="flex items-center gap-3 border border-slate-200 rounded-lg p-3 hover:bg-slate-50 no-underline transition-colors duration-150 active:scale-[0.98]">
              <AppIcon name="Upload" :size="18" class="text-primary-500" />
              <span class="text-sm font-medium text-slate-700">我的贡献</span>
            </NuxtLink>
            <NuxtLink to="/user/bookmarks" class="flex items-center gap-3 border border-slate-200 rounded-lg p-3 hover:bg-slate-50 no-underline transition-colors duration-150 active:scale-[0.98]">
              <AppIcon name="Bookmark" :size="18" class="text-primary-500" />
              <span class="text-sm font-medium text-slate-700">收藏与关注</span>
            </NuxtLink>
            <NuxtLink to="/user/privacy" class="flex items-center gap-3 border border-slate-200 rounded-lg p-3 hover:bg-slate-50 no-underline transition-colors duration-150 active:scale-[0.98]">
              <AppIcon name="Shield" :size="18" class="text-primary-500" />
              <span class="text-sm font-medium text-slate-700">隐私设置</span>
            </NuxtLink>
          </div>
        </div>
        <BadgeWall />
      </div>

      <div v-else class="text-center py-16 px-4">
        <div class="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-6">
          <AppIcon name="User" :size="40" class="text-primary-300" />
        </div>
        <h2 class="text-lg font-semibold text-slate-800 mb-2">登录以查看个人中心</h2>
        <p class="text-sm text-slate-500 mb-6">登录后可查看贡献、收藏和浏览记录</p>
        <button class="inline-flex items-center gap-2 h-10 px-6 rounded-lg text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer transition-colors" @click="auth.openLogin()">
          <AppIcon name="LogIn" :size="16" /> 登录 / 注册
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()

// No auth middleware — this page handles both logged-in and logged-out states

const showEdit = ref(false)
const saving = ref(false)
const editForm = ref({ nickname: '' })

interface RecentItem {
  id: string
  type: string
  title: string
  url: string
  time: string
}

const recentItems = ref<RecentItem[]>([])

const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    student: '学生',
    contributor: '贡献者',
    maintainer: '维护者',
    admin: '管理员',
  }
  return labels[auth.user?.role || ''] || auth.user?.role || ''
})

watch(() => auth.authChecked, (checked) => {
  if (checked && !auth.isLoggedIn) auth.openLogin()
})

onMounted(() => {
  if (auth.isLoggedIn) editForm.value.nickname = auth.user?.nickname || ''
  try {
    const raw = localStorage.getItem('scustack_recent')
    if (raw) recentItems.value = JSON.parse(raw)
  } catch { /* ignore */ }
})

async function handleSave() {
  saving.value = true
  try {
    await auth.updateProfile({ nickname: editForm.value.nickname })
    // Also update via direct call for immediate feedback
    const { updateProfile } = useAuth()
    await updateProfile({ nickname: editForm.value.nickname })
    showEdit.value = false
  } catch { /* noop */ }
  saving.value = false
}

function formatDate(_id: string) {
  return '2026年' // Simplified — real date would come from API
}
</script>
