<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 text-primary-800 font-semibold text-lg no-underline">
          <AppIcon name="GraduationCap" :size="24" />
          <span>川大课栈</span>
        </NuxtLink>
        <nav class="flex items-center gap-4">
          <NuxtLink to="/search" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
            搜索
          </NuxtLink>
          <div class="relative" @mouseenter="showColleges = true" @mouseleave="showColleges = false">
            <NuxtLink to="/colleges" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
              学院
            </NuxtLink>
            <div
              v-if="showColleges && collegeList.length"
              class="absolute top-full left-0 mt-1 w-48 bg-white border border-slate-200 rounded-md shadow z-50 max-h-64 overflow-y-auto"
            >
              <NuxtLink
                v-for="c in collegeList"
                :key="c.id"
                :to="`/colleges/${c.id}`"
                class="block px-3 py-2 text-sm text-slate-700 hover:bg-primary-50 no-underline"
              >
                {{ c.name }}
              </NuxtLink>
            </div>
          </div>
          <NuxtLink to="/upload" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
            上传
          </NuxtLink>
          <template v-if="auth.isLoggedIn">
            <NuxtLink to="/user/profile" class="text-sm text-slate-600 hover:text-primary-600 no-underline">
              {{ auth.user?.nickname }}
            </NuxtLink>
            <button class="text-sm text-slate-500 hover:text-slate-700 cursor-pointer" @click="auth.doLogout()">
              退出
            </button>
          </template>
          <button
            v-else
            class="text-sm text-primary-700 hover:text-primary-800 font-medium cursor-pointer"
            @click="auth.openLogin()"
          >
            登录
          </button>
        </nav>
      </div>
    </header>

    <LoginModal />

    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
const { apiBase } = useRuntimeConfig().public
const showColleges = ref(false)
const collegeList = ref<{ id: string; name: string }[]>([])

onMounted(async () => {
  await auth.fetchUser()
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
  if (resp.code === 0) collegeList.value = resp.data
})
</script>
