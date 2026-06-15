<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 class="text-2xl font-semibold text-slate-900 mb-2">{{ college?.name }}</h1>
      <p class="text-sm text-slate-500 mb-6">共 {{ courses.length }} 门课程</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <NuxtLink
          v-for="c in courses"
          :key="c.id"
          :to="`/course/${c.id}`"
          class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer"
        >
          <h3 class="text-base font-medium text-slate-800">{{ c.name }}</h3>
          <p v-if="c.category" class="text-xs text-slate-400 mt-1">{{ c.category }}</p>
          <p v-if="c.credit" class="text-xs text-slate-400 mt-1">{{ c.credit }} 学分</p>
        </NuxtLink>
      </div>
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
      <div v-if="!loading && courses.length === 0" class="text-center py-16">
        <AppIcon name="BookOpen" :size="48" class="text-slate-300 mx-auto mb-4" />
        <p class="text-slate-500 font-medium mb-1">暂未收录课程</p>
        <p class="text-sm text-slate-400">该学院下还没有课程资料</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiBase } = useRuntimeConfig().public

const college = ref<{ id: string; name: string } | null>(null)
const courses = ref<{ id: string; name: string; category: string | null; credit: number | null }[]>([])
const loading = ref(true)

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: '学院列表', to: '/colleges' },
  { label: college.value?.name || '...' },
])

onMounted(async () => {
  const [collegeResp, courseResp] = await Promise.all([
    $fetch<{ code: number; data: { id: string; name: string } | null }>(`${apiBase}/api/v1/colleges/${route.params.id}`),
    $fetch<{ code: number; data: { id: string; name: string; category: string | null; credit: number | null }[] }>(`${apiBase}/api/v1/courses?college_id=${route.params.id}`),
  ])
  if (collegeResp.code === 0) college.value = collegeResp.data
  if (courseResp.code === 0) courses.value = courseResp.data
  loading.value = false
})
</script>
