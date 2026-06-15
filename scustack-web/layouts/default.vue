<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 text-primary-800 font-semibold text-lg no-underline">
          <AppIcon name="GraduationCap" :size="24" />
          <span>川大课栈</span>
        </NuxtLink>
        <nav class="flex items-center gap-4 flex-1 justify-center px-8">
          <SearchBar variant="nav" />
          <div class="relative" @mouseenter="showColleges = true" @mouseleave="showColleges = false">
            <NuxtLink to="/colleges" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
              学院
            </NuxtLink>
            <div
              v-if="showColleges && collegeList.length"
              class="absolute top-full left-0 mt-1 w-48 bg-white border border-slate-200 rounded-md shadow z-50 max-h-64 overflow-y-auto"
            >
              <NuxtLink
                v-for="c in collegeList"
                :key="c.id"
                :to="`/colleges/${c.id}`"
                class="block px-3 py-2 text-sm text-slate-700 hover:bg-primary-50 no-underline"
              >
                {{ c.name }}
              </NuxtLink>
            </div>
          </div>
          <NuxtLink to="/upload" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
            上传
          </NuxtLink>
          <template v-if="auth.isLoggedIn">
            <!-- Notification bell -->
            <div class="relative">
              <button
                class="relative cursor-pointer p-1 text-slate-500 hover:text-slate-700 transition-colors duration-150"
                @click="toggleNotifications"
              >
                <AppIcon name="Bell" :size="18" />
                <span
                  v-if="auth.unreadNotificationCount > 0"
                  class="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-medium"
                >
                  {{ auth.unreadNotificationCount > 9 ? '9+' : auth.unreadNotificationCount }}
                </span>
              </button>
              <!-- Notification dropdown -->
              <div
                v-if="showNotifications"
                class="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-lg z-50"
                @click.stop
              >
                <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                  <span class="text-sm font-medium text-slate-700">通知</span>
                  <button
                    v-if="notificationList.length > 0"
                    class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer"
                    @click="markAllRead"
                  >
                    全部已读
                  </button>
                </div>
                <div class="max-h-80 overflow-y-auto">
                  <div v-if="notificationList.length > 0">
                    <div
                      v-for="n in notificationList"
                      :key="n.id"
                      :class="[
                        'px-4 py-3 border-b border-slate-50 cursor-pointer hover:bg-slate-50 transition-colors duration-150',
                        !n.is_read && 'bg-primary-50/50',
                      ]"
                      @click="handleNotificationClick(n)"
                    >
                      <p class="text-sm text-slate-700">{{ n.title }}</p>
                      <p v-if="n.body" class="text-xs text-slate-500 mt-0.5 line-clamp-1">{{ n.body }}</p>
                      <p class="text-xs text-slate-400 mt-1">{{ formatNotifTime(n.created_at) }}</p>
                    </div>
                  </div>
                  <div v-else class="px-4 py-8 text-center">
                    <AppIcon name="Bell" :size="32" class="text-slate-300 mx-auto mb-2" />
                    <p class="text-xs text-slate-400">暂无通知</p>
                  </div>
                </div>
              </div>
            </div>
            <NuxtLink to="/user/profile" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
              {{ auth.user?.nickname }}
            </NuxtLink>
            <button class="text-sm text-slate-500 hover:text-slate-700 cursor-pointer" @click="auth.doLogout()">
              退出
            </button>
          </template>
          <button
            v-else
            class="text-sm text-primary-700 hover:text-primary-800 font-medium cursor-pointer"
            @click="auth.openLogin()"
          >
            登录
          </button>
        </nav>
      </div>
    </header>

    <LoginModal />

    <!-- Notification click overlay -->
    <div v-if="showNotifications" class="fixed inset-0 z-40" @click="showNotifications = false" />

    <main>
      <slot />
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const { apiBase } = useRuntimeConfig().public
const showColleges = ref(false)
const collegeList = ref<{ id: string; name: string }[]>([])
const showNotifications = ref(false)
const notificationList = ref<any[]>([])

onMounted(async () => {
  await auth.fetchUser()
  await auth.fetchUnreadCount()
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
  if (resp.code === 0) collegeList.value = resp.data
})

async function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    await loadNotifications()
  }
}

async function loadNotifications() {
  const { getNotifications } = useAuth()
  try {
    const resp = await getNotifications(10, 0)
    if (resp.code === 0) {
      notificationList.value = resp.data.items
      auth.unreadNotificationCount = resp.data.unread_count
    }
  } catch { /* noop */ }
}

async function handleNotificationClick(n: any) {
  const { markNotificationRead } = useAuth()
  if (!n.is_read) {
    await markNotificationRead(n.id)
    n.is_read = true
    if (auth.unreadNotificationCount > 0) auth.unreadNotificationCount--
  }
  showNotifications.value = false
  if (n.resource_type === 'material' && n.resource_id) {
    navigateTo(`/material/${n.resource_id}`)
  } else if (n.resource_type === 'course' && n.resource_id) {
    navigateTo(`/course/${n.resource_id}`)
  }
}

async function markAllRead() {
  const { markAllNotificationsRead } = useAuth()
  await markAllNotificationsRead()
  notificationList.value.forEach(n => { n.is_read = true })
  auth.unreadNotificationCount = 0
}

function formatNotifTime(d: string) {
  const date = new Date(d)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return date.toLocaleDateString('zh-CN')
}
</script>
