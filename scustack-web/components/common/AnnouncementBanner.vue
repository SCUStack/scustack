<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="current"
        class="fixed inset-x-0 bottom-0 z-[100] bg-white border-t shadow-2xl rounded-t-2xl"
        :class="severityBorder(current.severity)"
        style="max-height: 30vh"
      >
        <!-- Handle bar -->
        <div class="flex justify-center pt-2 pb-1">
          <div class="w-10 h-1 rounded-full bg-slate-300" />
        </div>

        <div class="px-5 pb-5 overflow-y-auto" style="max-height: calc(30vh - 28px)">
          <div class="flex items-start justify-between gap-3 mb-1">
            <div class="flex items-center gap-2">
              <span :class="['inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium', severityBadge(current.severity)]">
                <AppIcon :name="severityIcon(current.severity)" :size="12" />
                {{ severityLabel(current.severity) }}
              </span>
            </div>
            <button class="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors border-none bg-transparent" @click="dismissCurrent">
              <AppIcon name="X" :size="16" />
            </button>
          </div>

          <h3 class="text-base font-semibold text-slate-900 mt-2 mb-1">{{ current.title }}</h3>
          <p v-if="current.content" class="text-sm text-slate-600 leading-relaxed mb-3">{{ current.content }}</p>

          <div class="flex gap-2">
            <NuxtLink
              v-if="current.action_text && current.action_url"
              :to="current.action_url"
              class="inline-flex items-center gap-1 h-9 px-5 rounded-md text-sm font-medium no-underline transition-colors cursor-pointer"
              :class="severityButton(current.severity)"
              @click="dismissCurrent"
            >{{ current.action_text }}</NuxtLink>
            <button class="h-9 px-4 rounded-md text-sm text-slate-500 hover:bg-slate-100 cursor-pointer transition-colors border-none bg-transparent" @click="dismissCurrent">关闭</button>
          </div>

          <!-- Dot indicators for multiple -->
          <div v-if="activeAnnouncements.length > 1" class="flex justify-center gap-1.5 mt-4">
            <button
              v-for="(a, i) in activeAnnouncements" :key="a.id"
              class="w-2 h-2 rounded-full border-none cursor-pointer transition-all"
              :class="i === currentIndex ? 'bg-primary-500 w-4' : 'bg-slate-300 hover:bg-slate-400'"
              @click="currentIndex = i"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public
const activeAnnouncements = ref<any[]>([])
const currentIndex = ref(0)

const current = computed(() => activeAnnouncements.value[currentIndex.value] || null)

function severityBorder(s: string): string {
  return { info: 'border-t-4 border-t-blue-500', success: 'border-t-4 border-t-emerald-500', warning: 'border-t-4 border-t-amber-500' }[s] || 'border-t-4 border-t-blue-500'
}
function severityBadge(s: string): string {
  return { info: 'bg-blue-50 text-blue-700', success: 'bg-emerald-50 text-emerald-700', warning: 'bg-amber-50 text-amber-700' }[s] || 'bg-blue-50 text-blue-700'
}
function severityButton(s: string): string {
  return { info: 'bg-blue-600 text-white hover:bg-blue-700', success: 'bg-emerald-600 text-white hover:bg-emerald-700', warning: 'bg-amber-500 text-amber-900 hover:bg-amber-600' }[s] || 'bg-blue-600 text-white hover:bg-blue-700'
}
function severityIcon(s: string): string {
  return { info: 'Info', success: 'CheckCircle', warning: 'Megaphone' }[s] || 'Info'
}
function severityLabel(s: string): string {
  return { info: '通知', success: '好消息', warning: '重要' }[s] || '通知'
}

function dismissCurrent() {
  if (!current.value) return
  try { localStorage.setItem('scustack_dismissed:' + current.value.id, new Date().toDateString()) } catch {}
  // Remove current and advance
  activeAnnouncements.value = activeAnnouncements.value.filter(a => a.id !== current.value.id)
  if (currentIndex.value >= activeAnnouncements.value.length) currentIndex.value = 0
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

<style scoped>
.drawer-enter-active { transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1); }
.drawer-leave-active { transition: transform 0.25s cubic-bezier(0.32, 0.72, 0, 1); }
.drawer-enter-from, .drawer-leave-to { transform: translateY(100%); }
</style>
