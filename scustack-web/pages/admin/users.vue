<template>
  <NuxtLayout name="admin">
    <div>
      <h1 class="text-xl font-semibold text-slate-900 mb-1">用户管理</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ total }} 位用户</p>

      <div class="mb-4 flex items-center gap-3 flex-wrap">
        <input v-model="searchQuery" placeholder="搜索手机号/昵称..." class="w-56 h-9 px-3 border border-slate-200 rounded-md text-sm" @input="debounceSearch" />
        <select v-model="roleFilter" class="h-9 px-3 border border-slate-200 rounded-md text-sm" @change="loadUsers">
          <option value="">全部角色</option>
          <option value="student">学生</option>
          <option value="contributor">贡献者</option>
          <option value="maintainer">维护者</option>
          <option value="admin">管理员</option>
        </select>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        <div v-for="u in users" :key="u.id" class="px-4 py-3 flex items-center gap-4">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ u.nickname }}</p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ roleLabel(u.role) }} · 信任分 {{ u.trust_score }}
              <span :class="u.is_active ? 'text-emerald-500' : 'text-red-500'" class="ml-1">· {{ u.is_active ? '正常' : '已封禁' }}</span>
              <span class="ml-1">· {{ formatDate(u.created_at) }}</span>
            </p>
          </div>
          <select :value="u.role" class="h-8 px-2 border border-slate-200 rounded text-xs" @change="changeRole(u.id, ($event.target as HTMLSelectElement).value)">
            <option value="student">学生</option>
            <option value="contributor">贡献者</option>
            <option value="maintainer">维护者</option>
            <option value="admin">管理员</option>
          </select>
          <button
            :class="['h-8 px-3 rounded text-xs font-medium cursor-pointer', u.is_active ? 'text-red-500 hover:bg-red-50' : 'text-emerald-600 hover:bg-emerald-50']"
            @click="toggleBan(u)"
          >
            {{ u.is_active ? '封禁' : '解封' }}
          </button>
        </div>
        <div v-if="users.length === 0" class="px-4 py-12 text-center text-sm text-slate-400">未找到用户</div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const users = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const searchQuery = ref('')
const roleFilter = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

function debounceSearch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadUsers, 300)
}

async function loadUsers() {
  loading.value = true
  const params = new URLSearchParams()
  if (searchQuery.value) params.set('q', searchQuery.value)
  if (roleFilter.value) params.set('role', roleFilter.value)
  params.set('limit', '50')
  try {
    const resp = await $fetch<{ code: number; data: { items: any[]; total: number } }>(
      `${apiBase}/api/v1/admin/users?${params.toString()}`,
      { credentials: 'include' },
    )
    if (resp.code === 0) {
      users.value = resp.data.items
      total.value = resp.data.total
    }
  } catch { /* noop */ }
  loading.value = false
}

async function changeRole(userId: string, role: string) {
  await $fetch(`${apiBase}/api/v1/admin/users/${userId}?role=${role}`, {
    method: 'PATCH', credentials: 'include',
  })
  await loadUsers()
}

async function toggleBan(u: any) {
  await $fetch(`${apiBase}/api/v1/admin/users/${u.id}?is_active=${!u.is_active}`, {
    method: 'PATCH', credentials: 'include',
  })
  await loadUsers()
}

function roleLabel(role: string) {
  const m: Record<string, string> = { student: '学生', contributor: '贡献者', maintainer: '维护者', admin: '管理员' }
  return m[role] || role
}

function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }

onMounted(loadUsers)
</script>
