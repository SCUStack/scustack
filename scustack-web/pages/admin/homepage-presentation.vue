<template>
  <NuxtLayout name="admin">
    <div>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 class="text-xl font-semibold text-slate-900 mb-1">首页展示配置</h1>
          <p class="text-sm text-slate-500">维护首页 banner，无需再改前端硬编码。</p>
        </div>
        <button class="h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 cursor-pointer" @click="addBanner">新增 Banner</button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else class="space-y-4">
        <div v-for="(banner, idx) in banners" :key="idx" class="bg-white border border-slate-200 rounded-lg p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-slate-800">Banner {{ idx + 1 }}</h2>
            <button class="text-xs text-red-500 hover:text-red-600 cursor-pointer" @click="removeBanner(idx)">删除</button>
          </div>
          <div class="grid gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">图片地址</label>
              <input v-model="banner.image" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" placeholder="/banners/b1.jpg" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">标题</label>
              <input v-model="banner.title" maxlength="100" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">副标题</label>
              <input v-model="banner.subtitle" maxlength="160" class="w-full h-9 px-3 border border-slate-200 rounded-md text-sm" />
            </div>
          </div>
        </div>

        <div class="flex justify-end">
          <button
            class="h-10 px-5 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer"
            :disabled="saving || !canSave"
            @click="save"
          >
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { apiBase } = useRuntimeConfig().public
const loading = ref(true)
const saving = ref(false)
const banners = ref<Array<{ image: string; title: string; subtitle: string }>>([])

const canSave = computed(() =>
  banners.value.length > 0
  && banners.value.every(b => b.image.trim() && b.title.trim() && b.subtitle.trim()),
)

function addBanner() {
  banners.value.push({ image: '', title: '', subtitle: '' })
}

function removeBanner(index: number) {
  banners.value.splice(index, 1)
}

async function loadData() {
  loading.value = true
  try {
    const resp = await $fetch<{ code: number; data: { banners: Array<{ image: string; title: string; subtitle: string }> } }>(
      `${apiBase}/api/v1/admin/homepage-presentation`,
      { credentials: 'include' },
    )
    if (resp.code === 0) banners.value = resp.data.banners || []
  } catch { /* noop */ }
  loading.value = false
}

async function save() {
  saving.value = true
  try {
    await $fetch(`${apiBase}/api/v1/admin/homepage-presentation`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ banners: banners.value }),
    })
  } catch { /* noop */ }
  saving.value = false
}

onMounted(loadData)
</script>
