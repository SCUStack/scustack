<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="pending" class="flex justify-center py-12">
        <div class="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>

      <div v-else-if="loadFailed" class="py-16 text-center">
        <AppIcon name="WifiOff" :size="48" class="mb-4 text-slate-300" />
        <p class="mb-4 text-slate-500">学院课程加载失败</p>
        <button
          type="button"
          class="h-10 rounded-md bg-primary-700 px-5 text-sm font-medium text-white hover:bg-primary-800"
          @click="() => refresh()"
        >
          重新加载
        </button>
      </div>

      <template v-else-if="college">
        <div class="mb-8">
          <h1 class="text-2xl font-semibold text-slate-900 mb-2">{{ college.name }}</h1>
          <p v-if="college.description" class="text-sm text-slate-500 max-w-2xl mb-3">{{ college.description }}</p>
          <div class="flex flex-wrap gap-3 text-sm text-slate-500">
            <span class="inline-flex items-center gap-1">
              <AppIcon name="BookOpen" :size="14" />
              {{ college.course_count ?? courses.length }} 门课程
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

        <h2 class="mb-4 text-lg font-semibold text-slate-800">课程合集</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <NuxtLink
            v-for="c in courses"
            :key="c.id"
            :to="`/course/${c.id}`"
            class="block min-h-32 rounded-lg border border-slate-200 bg-white p-4 no-underline transition-all duration-200 hover:border-primary-200 hover:shadow-sm"
          >
            <h3 class="text-base font-medium text-slate-800">{{ c.name }}</h3>
            <p class="mt-1 text-xs text-slate-400">
              <span v-if="c.category">{{ c.category }}</span>
              <span v-if="c.category && c.credit"> · </span>
              <span v-if="c.credit">{{ c.credit }} 学分</span>
            </p>
            <p v-if="c.description" class="mt-3 line-clamp-2 text-sm leading-6 text-slate-500">
              {{ c.description }}
            </p>
          </NuxtLink>
        </div>
        <EmptyState v-if="courses.length === 0" icon="BookOpen" title="暂未收录课程" description="该学院下还没有课程资料" />
      </template>

      <div v-else class="text-center py-12">
        <AppIcon name="Building2" :size="48" class="text-slate-300 mb-4" />
        <p class="text-slate-500 mb-2">学院不存在</p>
        <NuxtLink to="/colleges" class="text-sm text-primary-600 hover:text-primary-700 no-underline">返回学院列表</NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

interface CollegeDetail {
  id: string
  name: string
  description: string | null
  website: string | null
  course_count: number
  material_count: number
}

interface CollegeCourse {
  id: string
  name: string
  category: string | null
  credit: number | null
  description: string | null
}

const route = useRoute()
const { apiBase } = useRuntimeConfig().public
const collegeId = String(route.params.id)
const isValidCollegeId = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(collegeId)

const { data, pending, refresh } = await useAsyncData(
  `college-detail-${collegeId}`,
  async () => {
    if (!isValidCollegeId) {
      return { college: null, courses: [], loadFailed: false }
    }
    try {
      const [collegeResp, courseResp] = await Promise.all([
        $fetch<{ code: number; data: CollegeDetail | null }>(`${apiBase}/api/v1/colleges/${collegeId}`),
        $fetch<{ code: number; data: CollegeCourse[] }>(`${apiBase}/api/v1/courses?college_id=${collegeId}`),
      ])
      return {
        college: collegeResp.code === 0 ? collegeResp.data : null,
        courses: courseResp.code === 0 ? courseResp.data : [],
        loadFailed: false,
      }
    } catch {
      return { college: null, courses: [], loadFailed: true }
    }
  },
)

const college = computed(() => data.value?.college ?? null)
const courses = computed(() => data.value?.courses ?? [])
const loadFailed = computed(() => data.value?.loadFailed ?? false)

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: '学院列表', to: '/colleges' },
  { label: college.value?.name || '...' },
])
</script>
