<template>
  <header
    class="fixed inset-x-0 top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur"
    style="padding-top: var(--safe-area-top); padding-left: var(--safe-area-left); padding-right: var(--safe-area-right)"
  >
    <div class="flex h-14 items-center gap-2 px-3">
      <button
        type="button"
        aria-label="返回上一页"
        class="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
        @click="goBack"
      >
        <AppIcon name="ArrowLeft" :size="20" />
      </button>
      <h1 class="min-w-0 flex-1 truncate text-base font-semibold text-slate-900">{{ title }}</h1>
      <NuxtLink
        to="/search"
        aria-label="搜索课程和资料"
        class="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-slate-600 no-underline transition-colors hover:bg-slate-100 hover:text-slate-900"
      >
        <AppIcon name="Search" :size="20" />
      </NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ title: string }>()

const router = useRouter()

function goBack() {
  if (window.history.length > 1) router.back()
  else navigateTo('/')
}
</script>
