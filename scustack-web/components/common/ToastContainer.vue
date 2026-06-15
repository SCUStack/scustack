<template>
  <Teleport to="body">
    <TransitionGroup
      name="toast"
      tag="div"
      class="fixed z-[100] flex flex-col gap-2 pointer-events-none"
      :class="isMobile ? 'top-4 left-4 right-4 items-center' : 'top-4 right-4 items-end'"
      role="alert"
      aria-live="polite"
    >
      <div
        v-for="t in toastList"
        :key="t.id"
        class="pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-lg border text-sm max-w-sm cursor-pointer"
        :class="toastClass(t.type)"
        @click="remove(t.id)"
      >
        <AppIcon :name="toastIcon(t.type)" :size="16" class="shrink-0" />
        <span class="flex-1">{{ t.message }}</span>
        <button class="shrink-0 opacity-50 hover:opacity-100 cursor-pointer" @click.stop="remove(t.id)">
          <AppIcon name="X" :size="14" />
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup lang="ts">
const { toasts, remove } = useToast()

const isMobile = ref(false)
function checkMobile() { isMobile.value = window.innerWidth < 640 }
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const toastList = toasts

function toastClass(type: string) {
  switch (type) {
    case 'success': return 'bg-green-50 border-green-200 text-green-800'
    case 'warning': return 'bg-amber-50 border-amber-200 text-amber-800'
    case 'error': return 'bg-red-50 border-red-200 text-red-800'
    default: return 'bg-blue-50 border-blue-200 text-blue-800'
  }
}

function toastIcon(type: string) {
  switch (type) {
    case 'success': return 'CircleCheck'
    case 'warning': return 'AlertTriangle'
    case 'error': return 'XCircle'
    default: return 'Info'
  }
}
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(2rem); }
.toast-leave-to { opacity: 0; transform: translateX(2rem); }
</style>
