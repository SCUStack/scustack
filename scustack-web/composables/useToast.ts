import { readonly, ref } from 'vue'

export interface Toast {
  id: number
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
  duration: number
}

const toasts = ref<Toast[]>([])
let nextId = 0

export function useToast() {
  function add(type: Toast['type'], message: string, duration = 3000) {
    if (toasts.value.length >= 3) {
      toasts.value.shift()
    }
    const toast: Toast = { id: nextId++, type, message, duration }
    toasts.value.push(toast)
    if (duration > 0) {
      setTimeout(() => remove(toast.id), duration)
    }
  }

  function remove(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return {
    toasts: readonly(toasts),
    success: (msg: string, dur?: number) => add('success', msg, dur),
    warning: (msg: string, dur?: number) => add('warning', msg, dur),
    error: (msg: string, dur?: number) => add('error', msg, dur),
    info: (msg: string, dur?: number) => add('info', msg, dur),
    remove,
  }
}
