<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="close">
        <div class="absolute inset-0 bg-black/40" />
        <div class="relative bg-white rounded-lg shadow-lg w-full max-w-sm mx-4 p-6">
          <button class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 cursor-pointer" @click="close">
            <AppIcon name="X" :size="20" />
          </button>

          <h2 class="text-lg font-semibold text-slate-900 mb-4">{{ titleText }}</h2>

          <!-- Mode tabs -->
          <div class="flex border-b border-slate-200 mb-4">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="flex-1 pb-2 text-sm font-medium border-b-2 transition-colors duration-150 cursor-pointer"
              :class="mode === tab.key ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-400 hover:text-slate-600'"
              @click="switchMode(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>

          <!-- SMS login -->
          <template v-if="mode === 'sms' && smsStep === 'phone'">
            <form @submit.prevent="sendCode">
              <label class="block text-sm text-slate-600 mb-1">手机号</label>
              <input
                v-model="phone"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="输入手机号"
                maxlength="11"
              />
              <p v-if="errorMsg" class="text-sm text-red-500 mt-2">{{ errorMsg }}</p>
              <button
                type="submit"
                :disabled="loading || phone.length !== 11"
                class="w-full h-10 mt-4 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150 bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed"
              >
                {{ loading ? '发送中...' : '获取验证码' }}
              </button>
              <div class="mt-3 text-center">
                <button
                  type="button"
                  class="text-xs text-green-600 hover:text-green-700 cursor-pointer"
                  @click="wechatLogin"
                >
                  微信扫码登录
                </button>
              </div>
            </form>
          </template>

          <template v-if="mode === 'sms' && smsStep === 'code'">
            <p class="text-sm text-slate-500 mb-4">
              验证码已发送至 <span class="font-medium text-slate-700">{{ phone }}</span>
            </p>
            <form @submit.prevent="verifyCode">
              <label class="block text-sm text-slate-600 mb-1">验证码</label>
              <input
                v-model="code"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="输入6位验证码"
                maxlength="6"
                autocomplete="one-time-code"
              />
              <p v-if="errorMsg" class="text-sm text-red-500 mt-2">{{ errorMsg }}</p>
              <button
                type="submit"
                :disabled="loading || code.length !== 6"
                class="w-full h-10 mt-4 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150 bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed"
              >
                {{ loading ? '验证中...' : '登录' }}
              </button>
              <button
                type="button"
                :disabled="countdown > 0"
                class="w-full h-8 mt-2 text-xs text-primary-600 hover:text-primary-700 cursor-pointer disabled:text-slate-400 disabled:cursor-not-allowed"
                @click="sendCode"
              >
                {{ countdown > 0 ? `${countdown}s 后重新发送` : '重新发送验证码' }}
              </button>
            </form>
          </template>

          <!-- Password login -->
          <template v-if="mode === 'password'">
            <form @submit.prevent="doPasswordLogin">
              <label class="block text-sm text-slate-600 mb-1">手机号</label>
              <input
                v-model="phone"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="输入手机号"
                maxlength="11"
              />
              <label class="block text-sm text-slate-600 mb-1 mt-3">密码</label>
              <input
                v-model="password"
                type="password"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="输入密码"
                maxlength="128"
              />
              <p v-if="errorMsg" class="text-sm text-red-500 mt-2">{{ errorMsg }}</p>
              <button
                type="submit"
                :disabled="loading || phone.length !== 11 || !password"
                class="w-full h-10 mt-4 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150 bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed"
              >
                {{ loading ? '登录中...' : '登录' }}
              </button>
            </form>
          </template>

          <!-- Password register -->
          <template v-if="mode === 'register'">
            <form @submit.prevent="doPasswordRegister">
              <label class="block text-sm text-slate-600 mb-1">手机号</label>
              <input
                v-model="phone"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="输入手机号"
                maxlength="11"
              />
              <label class="block text-sm text-slate-600 mb-1 mt-3">密码</label>
              <input
                v-model="password"
                type="password"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="至少8位，含字母和数字"
                maxlength="128"
              />
              <label class="block text-sm text-slate-600 mb-1 mt-3">确认密码</label>
              <input
                v-model="confirmPassword"
                type="password"
                class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-colors duration-200"
                placeholder="再次输入密码"
                maxlength="128"
              />
              <p v-if="errorMsg" class="text-sm text-red-500 mt-2">{{ errorMsg }}</p>
              <label class="flex items-start gap-2 mt-4 cursor-pointer">
                <input
                  v-model="agreedToTerms"
                  type="checkbox"
                  class="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 cursor-pointer"
                />
                <span class="text-xs text-slate-500 leading-relaxed">
                  我已阅读并同意
                  <NuxtLink to="/terms" target="_blank" class="text-primary-600 hover:text-primary-700">《用户协议》</NuxtLink>
                  和
                  <NuxtLink to="/privacy" target="_blank" class="text-primary-600 hover:text-primary-700">《隐私政策》</NuxtLink>
                </span>
              </label>
              <button
                type="submit"
                :disabled="loading || phone.length !== 11 || !password || !confirmPassword || !agreedToTerms"
                class="w-full h-10 mt-4 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150 bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed"
              >
                {{ loading ? '注册中...' : '注册' }}
              </button>
            </form>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const visible = computed(() => authStore.isLoginModalOpen)

const tabs = [
  { key: 'sms', label: '短信登录' },
  { key: 'password', label: '密码登录' },
  { key: 'register', label: '注册' },
]
const mode = ref<'sms' | 'password' | 'register'>('sms')
const smsStep = ref<'phone' | 'code'>('phone')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreedToTerms = ref(false)
const code = ref('')
const loading = ref(false)
const errorMsg = ref('')
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const titleText = computed(() => {
  if (mode.value === 'register') return '注册账号'
  if (mode.value === 'sms' && smsStep.value === 'code') return '输入验证码'
  return '登录川流课栈'
})

function switchMode(key: string) {
  mode.value = key as typeof mode.value
  errorMsg.value = ''
  smsStep.value = 'phone'
  agreedToTerms.value = false
}

function close() {
  authStore.closeLogin()
  mode.value = 'sms'
  smsStep.value = 'phone'
  phone.value = ''
  password.value = ''
  confirmPassword.value = ''
  agreedToTerms.value = false
  code.value = ''
  errorMsg.value = ''
  loading.value = false
}

async function sendCode() {
  if (phone.value.length !== 11) return
  errorMsg.value = ''
  loading.value = true
  try {
    const { sendCode } = useAuth()
    const resp = await sendCode(phone.value)
    if (resp.code !== 0) {
      errorMsg.value = resp.message
    } else {
      smsStep.value = 'code'
      countdown.value = 60
      timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0 && timer) {
          clearInterval(timer)
          timer = null
        }
      }, 1000)
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function verifyCode() {
  if (code.value.length !== 6) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login(phone.value, code.value)
    close()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function doPasswordLogin() {
  if (phone.value.length !== 11 || !password.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.loginWithPassword(phone.value, password.value)
    close()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function doPasswordRegister() {
  if (phone.value.length !== 11 || !password.value || !confirmPassword.value) return
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
  if (!agreedToTerms.value) {
    errorMsg.value = '请阅读并同意用户协议和隐私政策'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.registerWithPassword(phone.value, password.value, confirmPassword.value)
    close()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '注册失败'
  } finally {
    loading.value = false
  }
}

async function wechatLogin() {
  const { getWechatUrl } = useAuth()
  const resp = await getWechatUrl()
  if (resp.code === 0 && resp.data.url) {
    window.location.href = resp.data.url
  } else {
    errorMsg.value = '微信登录暂不可用'
  }
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
