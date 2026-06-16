<template>
  <div
    v-for="a in activeAnnouncements"
    :key="a.id"
    :class="[
      'relative flex items-center justify-center gap-3 px-4 py-2.5 text-sm text-center transition-all duration-300',
      severityBg(a.severity),
      dismissed.has(a.id) && 'hidden',
    ]"
  >
    <span class="font-medium">{{ a.title }}</span>
    <span v-if="a.content" class="opacity-80 hidden sm:inline">{{ a.content }}</span>
    <NuxtLink
      v-if="a.action_text && a.action_url"
      :to="a.action_url"
      class="ml-1 px-2 py-0.5 rounded text-xs font-medium underline underline-offset-2 hover:opacity-80 transition-opacity"
      :class="severityLink(a.severity)"
    >{{ a.action_text }}</NuxtLink>
    <button
      class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded opacity-60 hover:opacity-100 cursor-pointer transition-opacity border-none bg-transparent"
      :class="severityClose(a.severity)"
      @click="dismiss(a.id)"
    >
      <AppIcon name="X" :size="14" />
    </button>
  </div>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public
const activeAnnouncements = ref<any[]>([])
const dismissed = ref(new Set<string>())

function severityBg(s: string): string {
  return { info: 'bg-blue-600 text-white', success: 'bg-emerald-600 text-white', warning: 'bg-amber-500 text-amber-900' }[s] || 'bg-blue-600 text-white'
}
function severityLink(s: string): string {
  return { info: 'text-white/90', success: 'text-white/90', warning: 'text-amber-900' }[s] || 'text-white/90'
}
function severityClose(s: string): string {
  return { info: 'text-white', success: 'text-white', warning: 'text-amber-900' }[s] || 'text-white'
}

function dismiss(id: string) {
  dismissed.value.add(id)
  try { localStorage.setItem('scustack_dismissed:' + id, new Date().toDateString()) } catch {}
}

onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: any[] }>(`${apiBase}/api/v1/announcements/active`)
    if (resp.code === 0) {
      const today = new Date().toDateString()
      activeAnnouncements.value = resp.data.filter((a: any) => {
        try { return localStorage.getItem('scustack_dismissed:' + a.id) !== today } catch { return true }
      })
    }
  } catch { /* noop */ }
})
</script>
