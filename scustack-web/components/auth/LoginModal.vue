<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45"
        @click.self="close"
      >
        <div
          ref="dialogRef"
          class="relative mx-4 w-full max-w-sm rounded-lg bg-white p-6 shadow-lg"
          role="dialog"
          aria-modal="true"
          aria-labelledby="login-modal-title"
          tabindex="-1"
          @keydown.esc.stop="close"
        >
          <button
            type="button"
            class="absolute right-3 top-3 flex h-11 w-11 items-center justify-center text-slate-400 transition-colors duration-150 hover:text-slate-700"
            aria-label="关闭"
            @click="close"
          >
            <AppIcon name="X" :size="20" />
          </button>

          <h2 id="login-modal-title" class="mb-4 pr-10 text-lg font-semibold text-slate-900">
            {{ mode === 'login' ? '登录川流课栈' : '验证川大学生身份' }}
          </h2>

          <div class="mb-5 grid grid-cols-2 border-b border-slate-200" role="tablist">
            <button
              v-for="tab in tabs"
              :id="`auth-tab-${tab.key}`"
              :key="tab.key"
              type="button"
              role="tab"
              :aria-selected="mode === tab.key"
              :aria-controls="`auth-panel-${tab.key}`"
              :class="[
                'h-11 border-b-2 text-sm font-medium transition-colors duration-150',
                mode === tab.key
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800',
              ]"
              @click="switchMode(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>

          <form
            v-if="mode === 'login'"
            id="auth-panel-login"
            role="tabpanel"
            aria-labelledby="auth-tab-login"
            @submit.prevent="doLogin"
          >
            <label for="login-university-id" class="mb-1 block text-sm text-slate-600">学号</label>
            <input
              id="login-university-id"
              ref="initialInputRef"
              v-model.trim="universityId"
              type="text"
              inputmode="numeric"
              autocomplete="username"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="输入川大学号"
              maxlength="14"
            />

            <label for="login-password" class="mb-1 mt-4 block text-sm text-slate-600">课栈密码</label>
            <input
              id="login-password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="输入课栈密码"
              maxlength="128"
            />

            <p v-if="errorMsg" role="alert" class="mt-3 text-sm text-red-500">{{ errorMsg }}</p>
            <button
              type="submit"
              :disabled="loading || !validUniversityId || !password"
              class="mt-5 h-11 w-full rounded-md bg-primary-700 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
            >
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>

          <form
            v-else
            id="auth-panel-register"
            role="tabpanel"
            aria-labelledby="auth-tab-register"
            @submit.prevent="doRegister"
          >
            <label for="register-university-id" class="mb-1 block text-sm text-slate-600">学号</label>
            <input
              id="register-university-id"
              ref="initialInputRef"
              v-model.trim="universityId"
              type="text"
              inputmode="numeric"
              autocomplete="username"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="输入川大学号"
              maxlength="14"
            />

            <label for="university-password" class="mb-1 mt-4 block text-sm text-slate-600">川大统一认证密码</label>
            <input
              id="university-password"
              v-model="universityPassword"
              type="password"
              autocomplete="off"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="仅用于本次身份校验"
              maxlength="128"
            />
            <p class="mt-1 text-xs leading-5 text-slate-500">川大密码不会保存，校验完成后立即丢弃。</p>

            <label for="register-password" class="mb-1 mt-3 block text-sm text-slate-600">设置课栈密码</label>
            <input
              id="register-password"
              v-model="password"
              type="password"
              autocomplete="new-password"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="至少8位，含字母和数字"
              maxlength="128"
            />

            <label for="confirm-password" class="mb-1 mt-4 block text-sm text-slate-600">确认课栈密码</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              class="h-11 w-full rounded-md border border-slate-200 px-3 text-sm outline-none transition-colors duration-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              placeholder="再次输入课栈密码"
              maxlength="128"
            />

            <p v-if="errorMsg" role="alert" class="mt-3 text-sm text-red-500">{{ errorMsg }}</p>
            <label class="mt-4 flex cursor-pointer items-start gap-2">
              <input
                v-model="agreedToTerms"
                type="checkbox"
                class="mt-0.5 h-5 w-5 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="text-xs leading-5 text-slate-500">
                我已阅读并同意
                <NuxtLink to="/terms" target="_blank" class="text-primary-600 hover:text-primary-700">《用户协议》</NuxtLink>
                和
                <NuxtLink to="/privacy" target="_blank" class="text-primary-600 hover:text-primary-700">《隐私政策》</NuxtLink>
              </span>
            </label>

            <button
              type="submit"
              :disabled="loading || !validUniversityId || !universityPassword || !password || !confirmPassword || !agreedToTerms"
              class="mt-4 h-11 w-full rounded-md bg-primary-700 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
            >
              {{ loading ? '验证并注册中...' : '验证身份并注册' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

type AuthMode = 'login' | 'register'

const authStore = useAuthStore()
const visible = computed(() => authStore.isLoginModalOpen)
const dialogRef = ref<HTMLElement | null>(null)
const initialInputRef = ref<HTMLInputElement | null>(null)
const tabs: { key: AuthMode; label: string }[] = [
  { key: 'login', label: '登录' },
  { key: 'register', label: '注册' },
]
const mode = ref<AuthMode>('login')
const universityId = ref('')
const universityPassword = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreedToTerms = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const validUniversityId = computed(() => /^\d{8,14}$/.test(universityId.value))

watch(visible, async (isVisible) => {
  if (!isVisible) return
  await focusInitialInput()
})

async function focusInitialInput() {
  await nextTick()
  initialInputRef.value?.focus()
}

function switchMode(nextMode: AuthMode) {
  mode.value = nextMode
  universityPassword.value = ''
  password.value = ''
  confirmPassword.value = ''
  agreedToTerms.value = false
  errorMsg.value = ''
  void focusInitialInput()
}

function close() {
  authStore.closeLogin()
  mode.value = 'login'
  universityId.value = ''
  universityPassword.value = ''
  password.value = ''
  confirmPassword.value = ''
  agreedToTerms.value = false
  errorMsg.value = ''
  loading.value = false
}

function errorMessage(error: unknown, fallback: string) {
  const fetchError = error as {
    data?: { message?: string }
    response?: { _data?: { message?: string } }
    message?: string
  }
  return fetchError.data?.message || fetchError.response?._data?.message || fetchError.message || fallback
}

async function doLogin() {
  if (!validUniversityId.value || !password.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.loginWithPassword(universityId.value, password.value)
    close()
  } catch (error: unknown) {
    errorMsg.value = errorMessage(error, '登录失败')
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  if (!validUniversityId.value || !universityPassword.value || !password.value) return
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的课栈密码不一致'
    return
  }
  if (!/^(?=.*[A-Za-z])(?=.*\d).{8,128}$/.test(password.value)) {
    errorMsg.value = '课栈密码至少8位，且需要包含字母和数字'
    return
  }
  if (!agreedToTerms.value) {
    errorMsg.value = '请阅读并同意用户协议和隐私政策'
    return
  }

  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.registerWithPassword(
      universityId.value,
      universityPassword.value,
      password.value,
      confirmPassword.value,
    )
    universityPassword.value = ''
    close()
  } catch (error: unknown) {
    universityPassword.value = ''
    errorMsg.value = errorMessage(error, '注册失败')
  } finally {
    loading.value = false
  }
}
</script>
