<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 h-14 flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 text-primary-800 font-semibold text-lg no-underline shrink-0">
          <AppIcon name="GraduationCap" :size="24" />
          <span class="hidden sm:inline">川流课栈 · 管理后台</span>
          <span class="sm:hidden text-sm">管理后台</span>
        </NuxtLink>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-500">{{ auth.user?.nickname }}</span>
          <NuxtLink to="/" class="text-xs text-slate-400 hover:text-primary-600 no-underline">返回前台</NuxtLink>
        </div>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
      <div class="lg:flex lg:gap-6">
        <nav class="lg:w-48 shrink-0 mb-4 lg:mb-0 sticky top-14 lg:top-0 z-30 bg-slate-50">
          <div class="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
            <NuxtLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap no-underline transition-colors duration-150',
                isActive(item.to) ? 'bg-primary-50 text-primary-700' : 'text-slate-600 hover:bg-slate-100',
              ]"
            >
              {{ item.label }}
              <span v-if="item.badge !== undefined && item.badge > 0" class="ml-1.5 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                {{ item.badge > 99 ? '99+' : item.badge }}
              </span>
            </NuxtLink>
          </div>
        </nav>
        <main class="flex-1 min-w-0">
          <slot />
        </main>
      </div>
    </div>
    <ToastContainer />
    <FeedbackButton />
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()

definePageMeta({ middleware: ['auth', 'role'], meta: { requiredRole: 'maintainer' } })

interface NavItem {
  label: string
  to: string
  badge?: number
}

const navItems: NavItem[] = [
  { label: '数据分析', to: '/admin/analytics' },
  { label: '审核队列', to: '/admin/review', badge: 0 },
  { label: '举报处理', to: '/admin/reports', badge: 0 },
  { label: '用户反馈', to: '/admin/feedback', badge: 0 },
  { label: '资料管理', to: '/admin/materials' },
  { label: '课程管理', to: '/admin/courses' },
  { label: '学院管理', to: '/admin/colleges' },
  { label: '用户管理', to: '/admin/users' },
  { label: '校历管理', to: '/admin/calendar' },
  { label: '全站通知', to: '/admin/announcements' },
  { label: '首页配置', to: '/admin/homepage-presentation' },
  { label: '屏蔽列表', to: '/admin/blocklist' },
  { label: '失效链接', to: '/admin/dead-links' },
  { label: '搜索分析', to: '/admin/search-analytics' },
  { label: '上传统计', to: '/admin/upload-stats' },
  { label: '存储监控', to: '/admin/storage' },
  { label: '安全监控', to: '/admin/security' },
  { label: '重复检测', to: '/admin/duplicates' },
  { label: '审计日志', to: '/admin/audit-logs' },
]

function isActive(to: string) {
  return route.path.startsWith(to)
}
</script>
