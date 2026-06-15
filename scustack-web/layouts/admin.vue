<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 h-14 flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 text-primary-800 font-semibold text-lg no-underline">
          <AppIcon name="GraduationCap" :size="24" />
          <span>川大课栈 · 管理后台</span>
        </NuxtLink>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-500">{{ auth.user?.nickname }}</span>
          <NuxtLink to="/" class="text-xs text-slate-400 hover:text-primary-600 no-underline">返回前台</NuxtLink>
        </div>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-6">
      <div class="lg:flex lg:gap-6">
        <nav class="lg:w-48 shrink-0 mb-4 lg:mb-0">
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
  { label: '课程管理', to: '/admin/courses' },
  { label: '学院管理', to: '/admin/colleges' },
  { label: '用户管理', to: '/admin/users' },
  { label: '校历管理', to: '/admin/calendar' },
  { label: '审计日志', to: '/admin/audit-logs' },
]

function isActive(to: string) {
  return route.path.startsWith(to)
}
</script>
