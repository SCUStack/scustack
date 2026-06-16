<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="pending" class="flex justify-center py-12">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <template v-else-if="college">
        <div class="mb-8">
          <h1 class="text-2xl font-semibold text-slate-900 mb-2">{{ college.name }}</h1>
          <p v-if="college.description" class="text-sm text-slate-500 max-w-2xl mb-3">{{ college.description }}</p>
          <div class="flex flex-wrap gap-3 text-sm text-slate-500">
            <span class="inline-flex items-center gap-1">
              <AppIcon name="BookOpen" :size="14" />
              {{ courses.length }} 门课程
            </span>
            <span v-if="college.material_count" class="inline-flex items-center gap-1">
              <AppIcon name="FileText" :size="14" />
              {{ college.material_count }} 份资料
            </span>
            <a v-if="college.website" :href="college.website" target="_blank" rel="noopener"
               class="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 no-underline">
              <AppIcon name="ExternalLink" :size="14" />
              学院官网
            </a>
          </div>
        </div>

        <h2 class="text-lg font-semibold text-slate-800 mb-4">开设课程</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <NuxtLink
            v-for="c in courses"
            :key="c.id"
            :to="`/course/${c.id}`"
            class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer"
          >
            <h3 class="text-base font-medium text-slate-800">{{ c.name }}</h3>
            <p v-if="c.category" class="text-xs text-slate-400 mt-1">{{ c.category }}<span v-if="c.credit"> · {{ c.credit }} 学分</span></p>
          </NuxtLink>
        </div>
        <EmptyState v-if="courses.length === 0" icon="BookOpen" title="暂未收录课程" description="该学院下还没有课程资料" />
      </template>

      <div v-else class="text-center py-12">
        <AppIcon name="Building2" size="48" class="text-slate-300 mb-4" />
        <p class="text-slate-500 mb-2">学院不存在</p>
        <NuxtLink to="/colleges" class="text-sm text-primary-600 hover:text-primary-700 no-underline">返回学院列表</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

const route = useRoute()
const { apiBase } = useRuntimeConfig().public

const { data, pending } = await useAsyncData(
  `college-detail-${route.params.id}`,
  async () => {
    const [collegeResp, courseResp] = await Promise.all([
      $fetch<{ code: number; data: Record<string, any> | null }>(`${apiBase}/api/v1/colleges/${route.params.id}`),
      $fetch<{ code: number; data: { id: string; name: string; category: string | null; credit: number | null; material_count?: number }[] }>(`${apiBase}/api/v1/courses?college_id=${route.params.id}`),
    ])
    return {
      college: collegeResp.code === 0 ? collegeResp.data : null,
      courses: courseResp.code === 0 ? courseResp.data : [],
    }
  },
)

const college = computed(() => data.value?.college ?? null)
const courses = computed(() => data.value?.courses ?? [])

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: '学院列表', to: '/colleges' },
  { label: college.value?.name || '...' },
])
</script>
