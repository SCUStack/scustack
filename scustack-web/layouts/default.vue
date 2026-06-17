<template>
  <div class="min-h-screen bg-slate-50">
    <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[200] focus:px-4 focus:py-2 focus:bg-primary-700 focus:text-white focus:rounded-md focus:no-underline">跳到主要内容</a>

    <!-- ═══════ DESKTOP NAVBAR ═══════ -->
    <header
      class="hidden lg:flex fixed top-0 left-0 right-0 z-50 h-14 items-center transition-all duration-300"
      :class="isHome && !scrolled
        ? 'bg-transparent text-white'
        : 'bg-white/95 backdrop-blur border-b border-slate-200 text-slate-800'"
    >
      <div class="flex items-center gap-4 pl-4">
        <NuxtLink to="/" class="flex items-center gap-1.5 font-semibold text-lg no-underline shrink-0" :class="isHome && !scrolled ? 'text-white' : 'text-primary-800'">
          <AppIcon name="GraduationCap" :size="22" />
          <span class="hidden sm:inline">川流课栈</span>
        </NuxtLink>
        <NuxtLink to="/" class="text-sm no-underline transition-colors duration-150" :class="isHome && !scrolled ? 'text-white/80 hover:text-white' : 'text-slate-700 hover:text-primary-600'">首页</NuxtLink>
        <NuxtLink to="/course" class="text-sm no-underline transition-colors duration-150" :class="isHome && !scrolled ? 'text-white/80 hover:text-white' : 'text-slate-700 hover:text-primary-600'">课程</NuxtLink>
        <NuxtLink to="/search" class="text-sm no-underline transition-colors duration-150" :class="isHome && !scrolled ? 'text-white/80 hover:text-white' : 'text-slate-700 hover:text-primary-600'">资料</NuxtLink>
        <NuxtLink to="/colleges" class="text-sm no-underline transition-colors duration-150" :class="isHome && !scrolled ? 'text-white/80 hover:text-white' : 'text-slate-700 hover:text-primary-600'">学院</NuxtLink>
        <NuxtLink to="/upload" class="text-sm no-underline transition-colors duration-150" :class="isHome && !scrolled ? 'text-white/80 hover:text-white' : 'text-slate-700 hover:text-primary-600'">上传</NuxtLink>
      </div>

      <div class="flex-1 flex justify-center px-4">
        <SearchBar variant="nav" placeholder="搜索课程、资料..." />
      </div>

      <div class="flex items-center gap-1 pr-4">
        <NuxtLink to="/upload" aria-label="上传" class="w-9 h-9 flex items-center justify-center rounded-md no-underline transition-colors duration-150"
          :class="isHome && !scrolled ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'">
          <AppIcon name="Upload" :size="18" />
        </NuxtLink>
        <NuxtLink to="/user/bookmarks" aria-label="收藏" class="w-9 h-9 flex items-center justify-center rounded-md no-underline transition-colors duration-150"
          :class="isHome && !scrolled ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'">
          <AppIcon name="Bookmark" :size="18" />
        </NuxtLink>
        <NuxtLink to="/user/contributions" aria-label="历史" class="w-9 h-9 flex items-center justify-center rounded-md no-underline transition-colors duration-150"
          :class="isHome && !scrolled ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'">
          <AppIcon name="History" :size="18" />
        </NuxtLink>

        <!-- Notification bell (desktop) -->
        <div class="relative">
          <button aria-label="通知"
            class="w-9 h-9 flex items-center justify-center rounded-md cursor-pointer transition-colors duration-150"
            :class="isHome && !scrolled ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'"
            @click="toggleNotifications">
            <AppIcon name="Bell" :size="18" />
            <span v-if="auth.isLoggedIn && auth.unreadNotificationCount > 0"
              class="absolute top-1 right-1.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-medium">
              {{ auth.unreadNotificationCount > 9 ? '9+' : auth.unreadNotificationCount }}
            </span>
          </button>
          <div v-if="showNotifications"
            class="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-lg z-50" @click.stop>
            <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
              <span class="text-sm font-medium text-slate-700">通知</span>
              <button v-if="notificationList.length > 0" class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer" @click="markAllRead">全部已读</button>
            </div>
            <div class="max-h-80 overflow-y-auto">
              <template v-if="notificationList.length > 0">
                <div v-for="n in notificationList" :key="n.id"
                  :class="['px-4 py-3 border-b border-slate-50 cursor-pointer hover:bg-slate-50 transition-colors duration-150', !n.is_read && 'bg-primary-50/50']"
                  @click="handleNotificationClick(n)">
                  <p class="text-sm text-slate-700">{{ n.title }}</p>
                  <p v-if="n.body" class="text-xs text-slate-500 mt-0.5 line-clamp-1">{{ n.body }}</p>
                  <p class="text-xs text-slate-400 mt-1">{{ formatNotifTime(n.created_at) }}</p>
                </div>
              </template>
              <EmptyState v-else icon="Bell" title="暂无通知" />
            </div>
          </div>
        </div>

        <!-- User avatar (desktop) -->
        <div class="relative" @click="auth.isLoggedIn ? (showUserMenu = !showUserMenu) : auth.openLogin()">
          <button class="flex items-center gap-1.5 cursor-pointer transition-colors duration-150 px-1 py-1 rounded-md"
            :class="isHome && !scrolled ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'">
            <div class="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden shrink-0"
              :class="isHome && !scrolled ? '!bg-white/20' : ''">
              <img v-if="auth.user?.avatarUrl" :src="auth.user.avatarUrl" class="w-full h-full object-cover" alt="" />
              <AppIcon v-else name="User" :size="16" :class="isHome && !scrolled ? 'text-white' : 'text-primary-600'" />
            </div>
            <span class="text-sm hidden sm:inline max-w-[80px] truncate">{{ auth.isLoggedIn ? auth.user?.nickname : '未登录' }}</span>
          </button>
          <div v-if="showUserMenu && auth.isLoggedIn"
            class="absolute right-0 top-full mt-2 w-56 bg-white border border-slate-200 rounded-lg shadow-lg z-50" @click.stop>
            <div class="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
              <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden shrink-0">
                <img v-if="auth.user?.avatarUrl" :src="auth.user.avatarUrl" class="w-full h-full object-cover" alt="" />
                <AppIcon v-else name="User" :size="20" class="text-primary-600" />
              </div>
              <div class="min-w-0">
                <p class="text-sm font-medium text-slate-800 truncate">{{ auth.user?.nickname }}</p>
                <p class="text-xs text-slate-400">信任分 {{ auth.user?.trustScore ?? 0 }}</p>
              </div>
            </div>
            <div class="py-1">
              <NuxtLink to="/user/profile" class="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 no-underline"><AppIcon name="User" :size="16" class="text-slate-400" />个人中心</NuxtLink>
              <NuxtLink to="/user/bookmarks" class="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 no-underline"><AppIcon name="Bookmark" :size="16" class="text-slate-400" />我的收藏</NuxtLink>
              <NuxtLink to="/user/contributions" class="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 no-underline"><AppIcon name="FileText" :size="16" class="text-slate-400" />我的贡献</NuxtLink>
              <NuxtLink to="/user/privacy" class="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 no-underline"><AppIcon name="Shield" :size="16" class="text-slate-400" />隐私设置</NuxtLink>
            </div>
            <div v-if="isAdmin" class="border-t border-slate-100 py-1">
              <NuxtLink to="/admin/review" class="flex items-center gap-3 px-4 py-2.5 text-sm text-primary-700 hover:bg-primary-50 no-underline"><AppIcon name="ShieldCheck" :size="16" class="text-primary-500" />管理后台</NuxtLink>
            </div>
            <div class="border-t border-slate-100 py-1">
              <button class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer" @click="auth.doLogout(); showUserMenu = false"><AppIcon name="LogOut" :size="16" class="text-slate-400" />退出登录</button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- ═══════ MOBILE NAVBAR (home only) ═══════ -->
    <header v-if="isHome" class="lg:hidden fixed top-0 left-0 right-0 z-50 h-14 flex items-center gap-1 px-3 bg-white/95 backdrop-blur border-b border-slate-200">
      <button class="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden shrink-0 cursor-pointer border-none" @click="navigateTo('/user/profile')">
        <img v-if="auth.user?.avatarUrl" :src="auth.user.avatarUrl" class="w-full h-full object-cover" alt="" />
        <AppIcon v-else name="User" :size="18" class="text-primary-600" />
      </button>

      <!-- Filter tabs -->
      <div class="flex-1 flex gap-5 overflow-x-auto no-scrollbar scroll-fade min-w-0 px-1">
        <button
          v-for="tab in homeTabs"
          :key="tab.key"
          class="relative shrink-0 py-2.5 text-sm font-medium transition-all duration-200 cursor-pointer border-none bg-transparent"
          :class="activeHomeTab === tab.key ? 'text-slate-900' : 'text-slate-400 hover:text-slate-600'"
          @click="setHomeTab(tab.key)"
        >
          {{ tab.label }}
          <span
            class="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 rounded-full bg-primary-600 transition-all duration-200"
            :class="activeHomeTab === tab.key ? 'w-5 opacity-100' : 'w-0 opacity-0'"
          />
        </button>
      </div>

      <button class="w-11 h-11 flex items-center justify-center rounded-lg cursor-pointer transition-colors duration-150 text-slate-600 hover:text-slate-800 hover:bg-slate-100 shrink-0" @click="navigateTo('/search')">
        <AppIcon name="Search" :size="20" />
      </button>

      <button
        class="relative w-11 h-11 flex items-center justify-center rounded-lg cursor-pointer transition-colors duration-150 text-slate-600 hover:text-slate-800 hover:bg-slate-100 shrink-0"
        @click="toggleNotifications">
        <AppIcon name="Bell" :size="20" />
        <span v-if="auth.isLoggedIn && auth.unreadNotificationCount > 0"
          class="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-medium">
          {{ auth.unreadNotificationCount > 9 ? '9+' : auth.unreadNotificationCount }}
        </span>
      </button>
      <!-- Mobile notification dropdown -->
      <div v-if="showNotifications"
        class="absolute right-3 top-full mt-1 w-72 bg-white border border-slate-200 rounded-lg shadow-lg z-50" @click.stop>
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <span class="text-sm font-medium text-slate-700">通知</span>
          <button v-if="notificationList.length > 0" class="text-xs text-primary-600 hover:text-primary-700 cursor-pointer" @click="markAllRead">全部已读</button>
        </div>
        <div class="max-h-80 overflow-y-auto">
          <template v-if="notificationList.length > 0">
            <div v-for="n in notificationList" :key="n.id"
              :class="['px-4 py-3 border-b border-slate-50 cursor-pointer hover:bg-slate-50 transition-colors duration-150', !n.is_read && 'bg-primary-50/50']"
              @click="handleNotificationClick(n)">
              <p class="text-sm text-slate-700">{{ n.title }}</p>
              <p v-if="n.body" class="text-xs text-slate-500 mt-0.5 line-clamp-1">{{ n.body }}</p>
              <p class="text-xs text-slate-400 mt-1">{{ formatNotifTime(n.created_at) }}</p>
            </div>
          </template>
          <EmptyState v-else icon="Bell" title="暂无通知" />
        </div>
      </div>
    </header>

    <!-- Notification / user menu overlay -->
    <div v-if="showNotifications || showUserMenu" class="fixed inset-0 z-40" @click="showNotifications = false; showUserMenu = false" />

    <LoginModal />
    <ToastContainer />
    <AnnouncementBanner />
    <FeedbackButton />

    <!-- Mobile bottom nav -->
    <nav class="lg:hidden fixed bottom-0 left-0 right-0 z-[60] h-14 bg-white/95 backdrop-blur border-t border-slate-200" style="padding-bottom: env(safe-area-inset-bottom, 0px)">
      <div class="h-full max-w-lg mx-auto flex items-center justify-around px-2">
        <NuxtLink to="/" class="flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 h-full no-underline transition-all duration-200 py-1"
          :class="route.path === '/' ? 'text-primary-600' : 'text-slate-400 hover:text-slate-600'">
          <AppIcon name="Home" :size="20" :class="route.path === '/' ? 'scale-110' : ''" />
          <span class="text-[10px] font-medium leading-none">首页</span>
        </NuxtLink>
        <NuxtLink to="/course" class="flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 h-full no-underline transition-all duration-200 py-1"
          :class="route.path.startsWith('/course') ? 'text-primary-600' : 'text-slate-400 hover:text-slate-600'">
          <AppIcon name="BookOpen" :size="20" :class="route.path.startsWith('/course') ? 'scale-110' : ''" />
          <span class="text-[10px] font-medium leading-none">课程</span>
        </NuxtLink>
        <NuxtLink to="/search" class="flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 h-full no-underline transition-all duration-200 py-1"
          :class="route.path.startsWith('/search') || route.path.startsWith('/material') ? 'text-primary-600' : 'text-slate-400 hover:text-slate-600'">
          <AppIcon name="Search" :size="20" :class="route.path.startsWith('/search') || route.path.startsWith('/material') ? 'scale-110' : ''" />
          <span class="text-[10px] font-medium leading-none">资料</span>
        </NuxtLink>
        <NuxtLink to="/colleges" class="flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 h-full no-underline transition-all duration-200 py-1"
          :class="route.path.startsWith('/colleges') ? 'text-primary-600' : 'text-slate-400 hover:text-slate-600'">
          <AppIcon name="Building2" :size="20" :class="route.path.startsWith('/colleges') ? 'scale-110' : ''" />
          <span class="text-[10px] font-medium leading-none">学院</span>
        </NuxtLink>
        <button class="flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 h-full transition-all duration-200 py-1 border-none bg-transparent cursor-pointer"
          :class="route.path.startsWith('/user') ? 'text-primary-600' : 'text-slate-400 hover:text-slate-600'"
          @click="goToProfile">
          <AppIcon name="User" :size="20" :class="route.path.startsWith('/user') ? 'scale-110' : ''" />
          <span class="text-[10px] font-medium leading-none">我的</span>
        </button>
      </div>
    </nav>

    <!-- Spacer: mobile home-only, desktop non-home only -->
    <div v-if="isHome" class="h-14 lg:hidden" />
    <div class="hidden lg:block" :class="isHome ? '' : 'h-14'" />

    <main id="main-content" class="pb-14 lg:pb-0">
      <slot />
    </main>

    <AppFooter class="hidden lg:block" />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const auth = useAuthStore()

const isHome = computed(() => route.path === '/')
const isAdmin = computed(() => {
  const role = auth.user?.role
  return role === 'maintainer' || role === 'admin'
})

const scrolled = ref(false)
const showNotifications = ref(false)
const showUserMenu = ref(false)
const homeTabs = [
  { key: 'recommend', label: '推荐' },
  { key: 'hot', label: '热门' },
  { key: 'newest', label: '最新' },
  { key: 'top', label: '高分' },
]
const activeHomeTab = useState<string>('home-active-tab', () => 'recommend')
function setHomeTab(key: string) { activeHomeTab.value = key }
const notificationList = ref<any[]>([])

useKeyboardShortcuts()

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  void auth.fetchUser().then(() => auth.fetchUnreadCount()).catch(() => {})
  window.addEventListener('close-all-overlays', () => {
    showNotifications.value = false
    showUserMenu.value = false
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})

function onScroll() {
  scrolled.value = window.scrollY > 64
}

async function toggleNotifications() {
  showUserMenu.value = false
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    try {
      const { getNotifications } = useAuth()
      const resp = await getNotifications(10, 0)
      if (resp.code === 0) {
        notificationList.value = resp.data.items
        auth.unreadNotificationCount = resp.data.unread_count
      }
    } catch { /* noop */ }
  }
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

function goToProfile() {
  navigateTo('/user/profile')
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
