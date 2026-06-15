<template>
  <div>
    <Breadcrumb :items="breadcrumbs" />
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="course" class="mb-6">
        <h1 class="text-2xl font-semibold text-slate-900 mb-1">{{ course.name }}</h1>
        <p v-if="course.aliases?.length" class="text-sm text-slate-500 mb-2">
          别名：{{ course.aliases.join('、') }}
        </p>
        <p class="text-sm text-slate-500">
          {{ course.college?.name }} · {{ course.category || '未分类' }}
          <span v-if="course.credit">· {{ course.credit }} 学分</span>
        </p>
        <div class="mt-3 flex items-center gap-3">
          <button
            @click="toggleFollow"
            :class="[
              'inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150',
              isFollowing ? 'bg-amber-50 text-amber-600 border border-amber-200' : 'border border-slate-200 text-slate-600 hover:bg-slate-50',
            ]"
          >
            <AppIcon :name="isFollowing ? 'BellRing' : 'Bell'" :size="14" />
            {{ isFollowing ? '已关注' : '关注课程' }}
          </button>
          <NuxtLink
            to="/upload"
            class="inline-flex items-center gap-1.5 h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors duration-150"
          >
            <AppIcon name="Upload" :size="14" /> 贡献资料
          </NuxtLink>
        </div>
      </div>

      <div class="flex items-center gap-3 mb-6">
        <div class="relative flex-1 max-w-md">
          <AppIcon name="Search" :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input v-model="inCourseQuery" placeholder="在课程内搜索..." class="w-full h-10 pl-9 pr-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                 @keydown.enter="searchInCourse" />
        </div>
        <select v-model="inCourseCategory" @change="searchInCourse" class="h-10 px-3 border border-slate-200 rounded-md text-sm">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="inCourseSemester" @change="searchInCourse" class="h-10 px-3 border border-slate-200 rounded-md text-sm">
          <option value="">全部学期</option>
          <option v-for="s in semesters" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="inCourseSort" @change="searchInCourse" class="h-10 px-3 border border-slate-200 rounded-md text-sm">
          <option value="relevance">相关度</option>
          <option value="newest">最新</option>
          <option value="downloads">最多下载</option>
          <option value="rating">最高评分</option>
        </select>
      </div>

      <div class="space-y-3">
        <MaterialCard v-for="item in materials" :key="item.id" :item="item" />
      </div>

      <div v-if="loading" class="py-8">
        <SkeletonList :count="4" />
      </div>

      <EmptyState v-if="!loading && materials.length === 0" icon="FolderOpen" title="该课程暂无资料" description="成为第一位贡献者" action-label="上传资料" action-to="/upload" />
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiBase } = useRuntimeConfig().public

const auth = useAuthStore()
const course = ref<any>(null)
const materials = ref<any[]>([])
const loading = ref(true)
const isFollowing = ref(false)

async function toggleFollow() {
  if (!auth.isLoggedIn) {
    auth.openLogin()
    return
  }
  const { toggleBookmark } = useAuth()
  try {
    await toggleBookmark(route.params.id as string, undefined)
    isFollowing.value = !isFollowing.value
  } catch { /* noop */ }
}
const inCourseQuery = ref('')
const inCourseCategory = ref('')
const inCourseSemester = ref('')
const inCourseSort = ref('relevance')
const categories = ['课堂笔记', '考试资料', '作业', '实验报告', '代码', '教材', '复习提纲', '其他']
const semesters = ['2026-2027-1', '2025-2026-2', '2025-2026-1', '2024-2025-2', '2024-2025-1']

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: course.value?.college?.name || '...', to: course.value ? `/colleges/${course.value.college_id}` : undefined },
  { label: course.value?.name || '...' },
])

async function searchInCourse() {
  loading.value = true
  const params = new URLSearchParams({
    course_id: route.params.id as string,
    sort: inCourseSort.value,
    page: '1', page_size: '20',
  })
  if (inCourseQuery.value) params.set('q', inCourseQuery.value)
  if (inCourseCategory.value) params.set('category', inCourseCategory.value)
  if (inCourseSemester.value) params.set('semester', inCourseSemester.value)

  const resp = await $fetch<{ code: number; data: { items: any[] } }>(`${apiBase}/api/v1/search?${params.toString()}`)
  if (resp.code === 0) materials.value = resp.data.items
  loading.value = false
}

function saveRecentCourse() {
  if (!course.value) return
  try {
    const raw = localStorage.getItem('scustack_recent')
    const list: any[] = raw ? JSON.parse(raw) : []
    const filtered = list.filter((i: any) => i.id !== course.value.id)
    filtered.unshift({
      id: course.value.id,
      type: 'course',
      title: course.value.name,
      url: `/course/${course.value.id}`,
      time: new Date().toLocaleDateString('zh-CN'),
    })
    localStorage.setItem('scustack_recent', JSON.stringify(filtered.slice(0, 20)))
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    const [courseResp, searchResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/courses/${route.params.id}`),
      $fetch<{ code: number; data: { items: any[] } }>(`${apiBase}/api/v1/search?course_id=${route.params.id}&page_size=20`),
    ])
    if (courseResp.code === 0) {
      course.value = courseResp.data
      saveRecentCourse()
    }
    if (searchResp.code === 0) materials.value = searchResp.data.items
  } catch { /* noop */ }
  loading.value = false
})
</script>
