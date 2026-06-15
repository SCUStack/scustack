<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="close">
        <div class="absolute inset-0 bg-black/40" />
        <div class="relative bg-white rounded-lg shadow-lg w-full max-w-sm mx-4 p-6">
          <button class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 cursor-pointer" @click="close">
            <AppIcon name="X" :size="20" />
          </button>

          <h2 class="text-lg font-semibold text-slate-900 mb-4">
            {{ step === 'phone' ? '手机号登录' : '输入验证码' }}
          </h2>

          <template v-if="step === 'phone'">
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
                <span class="text-xs text-slate-400">或</span>
                <button
                  type="button"
                  class="ml-2 text-xs text-green-600 hover:text-green-700 cursor-pointer"
                  @click="wechatLogin"
                >
                  微信扫码登录
                </button>
              </div>
            </form>
          </template>

          <template v-else>
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
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const visible = computed(() => authStore.isLoginModalOpen)

const step = ref<'phone' | 'code'>('phone')
const phone = ref('')
const code = ref('')
const loading = ref(false)
const errorMsg = ref('')
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

function close() {
  authStore.closeLogin()
  step.value = 'phone'
  phone.value = ''
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
      step.value = 'code'
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
