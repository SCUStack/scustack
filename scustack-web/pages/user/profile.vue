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
          <img
            :src="auth.user.avatarUrl || getDefaultAvatar(auth.user.id)"
            :alt="`${auth.user.nickname}的头像`"
            class="w-16 h-16 rounded-full bg-primary-100 object-cover shrink-0"
          />
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-medium text-slate-900">{{ auth.user.nickname }}</h2>
            <p class="text-sm text-slate-500 mt-0.5">
              {{ roleLabel }} · 信任分 {{ auth.user.trustScore }}
            </p>
            <p v-if="auth.user.universityIdMasked" class="text-xs text-slate-400 mt-0.5">
              学号 {{ auth.user.universityIdMasked }}
            </p>
            <p class="text-xs text-slate-400 mt-0.5">
              注册于 {{ formatDate(auth.user.createdAt) }}
            </p>
          </div>
          <button
            class="text-sm text-primary-600 hover:text-primary-700 font-medium cursor-pointer"
            @click="openEdit"
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

    </div>
    </div>

    <!-- Mobile -->
    <div class="lg:hidden px-4 pt-4 pb-4">
      <h1 class="text-lg font-semibold text-slate-900 mb-4">个人中心</h1>

      <div v-if="auth.user" class="space-y-4">
        <div class="bg-white border border-slate-200 rounded-xl p-4">
          <div class="flex items-start gap-3 mb-4">
            <img
              :src="auth.user.avatarUrl || getDefaultAvatar(auth.user.id)"
              :alt="`${auth.user.nickname}的头像`"
              class="w-14 h-14 rounded-full bg-primary-100 object-cover shrink-0"
            />
            <div class="flex-1 min-w-0">
              <h2 class="text-base font-medium text-slate-900">{{ auth.user.nickname }}</h2>
              <p class="text-xs text-slate-500 mt-0.5">{{ roleLabel }} · 信任分 {{ auth.user.trustScore }}</p>
              <p v-if="auth.user.universityIdMasked" class="text-xs text-slate-400 mt-0.5">学号 {{ auth.user.universityIdMasked }}</p>
            </div>
            <button class="text-xs text-primary-600 hover:text-primary-700 font-medium cursor-pointer" @click="openEdit">编辑</button>
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

    <div v-if="showEdit" role="dialog" aria-modal="true" aria-label="编辑个人资料" class="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center" @click.self="closeEdit">
      <div class="max-h-[calc(100dvh-2rem)] w-full max-w-sm overflow-y-auto rounded-lg bg-white p-6">
        <h3 class="text-base font-medium text-slate-900 mb-4">编辑资料</h3>
        <div class="space-y-4">
          <div>
            <span class="mb-2 block text-sm font-medium text-slate-700">头像</span>
            <div class="mb-3 flex items-center gap-3">
              <img
                :src="avatarPreviewUrl || editForm.avatarUrl"
                alt="头像预览"
                class="h-16 w-16 shrink-0 rounded-full bg-slate-100 object-cover"
              />
              <div>
                <input
                  ref="avatarInputRef"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  class="hidden"
                  @change="handleAvatarFile"
                />
                <button
                  type="button"
                  class="inline-flex h-11 cursor-pointer items-center gap-2 rounded-md border border-slate-200 px-3 text-sm text-slate-700 transition-colors hover:bg-slate-50 sm:h-9"
                  @click="avatarInputRef?.click()"
                >
                  <AppIcon name="Upload" :size="16" />
                  上传图片
                </button>
                <p class="mt-1 text-xs text-slate-400">PNG、JPEG 或 WebP，不超过 2 MB</p>
              </div>
            </div>
            <span class="mb-2 block text-xs text-slate-500">或选择默认头像</span>
            <div class="grid grid-cols-6 gap-2">
              <button
                v-for="avatar in DEFAULT_AVATARS"
                :key="avatar"
                type="button"
                :aria-label="`选择头像 ${avatar.split('-').at(-1)?.replace('.png', '')}`"
                :aria-pressed="editForm.avatarUrl === avatar"
                class="relative aspect-square cursor-pointer overflow-hidden rounded-full border-2 bg-slate-50 transition-colors"
                :class="editForm.avatarUrl === avatar ? 'border-primary-600' : 'border-transparent hover:border-slate-300'"
                @click="selectPresetAvatar(avatar)"
              >
                <img :src="avatar" alt="" class="h-full w-full object-cover" />
                <span
                  v-if="editForm.avatarUrl === avatar"
                  class="absolute inset-0 flex items-center justify-center bg-black/20 text-white"
                >
                  <AppIcon name="Check" :size="18" />
                </span>
              </button>
            </div>
            <p v-if="avatarError" role="alert" class="mt-2 text-xs text-red-500">{{ avatarError }}</p>
          </div>
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
              class="h-11 cursor-pointer rounded-md px-4 text-sm text-slate-600 transition-colors duration-150 hover:bg-slate-100 sm:h-9"
              @click="closeEdit"
            >
              取消
            </button>
            <button
              class="h-11 cursor-pointer rounded-md bg-primary-700 px-4 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary-800 sm:h-9"
              :disabled="saving"
              @click="handleSave"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
          <p v-if="saveError" role="alert" class="text-sm text-red-500">{{ saveError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { loadRecentViews, type RecentItem } from '~/composables/useLocalExperienceState'
import { DEFAULT_AVATARS, getDefaultAvatar } from '~/utils/defaultAvatar'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

const showEdit = ref(false)
const saving = ref(false)
const editForm = ref({ nickname: '', avatarUrl: '' })
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarFile = ref<File | null>(null)
const avatarPreviewUrl = ref('')
const avatarError = ref('')
const saveError = ref('')

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

onMounted(() => {
  recentItems.value = loadRecentViews()
})

function openEdit() {
  if (!auth.user) return
  clearAvatarPreview()
  editForm.value = {
    nickname: auth.user.nickname,
    avatarUrl: auth.user.avatarUrl || getDefaultAvatar(auth.user.id),
  }
  avatarError.value = ''
  saveError.value = ''
  showEdit.value = true
}

function clearAvatarPreview() {
  if (avatarPreviewUrl.value) URL.revokeObjectURL(avatarPreviewUrl.value)
  avatarPreviewUrl.value = ''
  avatarFile.value = null
}

function closeEdit() {
  clearAvatarPreview()
  showEdit.value = false
}

function selectPresetAvatar(avatar: string) {
  clearAvatarPreview()
  editForm.value.avatarUrl = avatar
  avatarError.value = ''
}

function handleAvatarFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    avatarError.value = '请选择 PNG、JPEG 或 WebP 图片'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    avatarError.value = '头像不能超过 2 MB'
    return
  }
  clearAvatarPreview()
  avatarFile.value = file
  avatarPreviewUrl.value = URL.createObjectURL(file)
  avatarError.value = ''
}

async function handleSave() {
  if (!editForm.value.nickname.trim()) {
    saveError.value = '昵称不能为空'
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    if (avatarFile.value) await auth.uploadAvatar(avatarFile.value)
    await auth.updateProfile({
      nickname: editForm.value.nickname.trim(),
      avatarUrl: avatarFile.value ? undefined : editForm.value.avatarUrl,
    })
    closeEdit()
  } catch (error: unknown) {
    const fetchError = error as { data?: { message?: string }; message?: string }
    saveError.value = fetchError.data?.message || fetchError.message || '资料保存失败'
  }
  saving.value = false
}

onUnmounted(clearAvatarPreview)

function formatDate(createdAt: string) {
  return new Date(createdAt).toLocaleDateString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>
