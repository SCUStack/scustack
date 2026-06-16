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
          <span v-if="total">· {{ total }} 份资料</span>
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

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MaterialCard v-for="item in materials" :key="item.id" :item="item" />
      </div>

      <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 py-8">
        <button
          :disabled="currentPage <= 1"
          class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
          @click="goToPage(currentPage - 1)"
        >
          上一页
        </button>
        <button
          v-for="p in pageNumbers"
          :key="p"
          :class="[
            'px-3 py-1.5 text-sm border rounded-md cursor-pointer transition-colors duration-150',
            p === currentPage ? 'bg-primary-500 text-white border-primary-500' : 'border-slate-200 hover:bg-slate-50 text-slate-600',
          ]"
          @click="goToPage(p)"
        >
          {{ p }}
        </button>
        <button
          :disabled="currentPage >= totalPages"
          class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
          @click="goToPage(currentPage + 1)"
        >
          下一页
        </button>
      </div>

      <div v-if="loading" class="py-8">
        <SkeletonList :count="4" />
      </div>

      <EmptyState v-if="!loading && materials.length === 0" icon="FolderOpen" title="该课程暂无资料" description="成为第一位贡献者" action-label="上传资料" action-to="/upload" />

      <WishList v-if="course" :course-id="course.id" />
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
const total = ref(0)
const PAGE_SIZE = 21

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
const categories = ['课堂笔记', '考试资料', '复习提纲', '教材', '习题集', '实验报告', '历年真题', '课件讲义']
const semesters = ['2026-2027-1', '2025-2026-2', '2025-2026-1', '2024-2025-2', '2024-2025-1']
const currentPage = ref(1)
const hasQueryFilters = computed(() => Boolean(inCourseQuery.value || inCourseCategory.value || inCourseSemester.value))
const totalPages = computed(() => Math.ceil(total.value / PAGE_SIZE) || 1)

const pageNumbers = computed(() => {
  const pages: number[] = []
  const tp = totalPages.value
  const cur = currentPage.value
  let start = Math.max(1, cur - 2)
  let end = Math.min(tp, cur + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(tp, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const breadcrumbs = computed(() => [
  { label: '首页', to: '/' },
  { label: course.value?.college?.name || '...', to: course.value ? `/colleges/${course.value.college_id}` : undefined },
  { label: course.value?.name || '...' },
])

async function fetchCourseMaterials(page = 1) {
  loading.value = true
  currentPage.value = page
  try {
    if (hasQueryFilters.value) {
      const params = new URLSearchParams({
        course_id: route.params.id as string,
        sort: inCourseSort.value,
        page: String(page),
        page_size: String(PAGE_SIZE),
      })
      if (inCourseQuery.value) params.set('q', inCourseQuery.value)
      if (inCourseCategory.value) params.set('category', inCourseCategory.value)
      if (inCourseSemester.value) params.set('semester', inCourseSemester.value)

      const resp = await $fetch<{ code: number; data?: { items?: any[]; total?: number } }>(`${apiBase}/api/v1/search?${params.toString()}`)
      const items = resp.code === 0 && Array.isArray(resp.data?.items) ? resp.data.items : []
      materials.value = items
      total.value = resp.code === 0 && typeof resp.data?.total === 'number' ? resp.data.total : items.length
      return
    }

    const offset = (page - 1) * PAGE_SIZE
    const params = new URLSearchParams({
      course_id: route.params.id as string,
      sort: inCourseSort.value === 'relevance' ? 'newest' : inCourseSort.value,
      limit: String(PAGE_SIZE),
      offset: String(offset),
    })
    if (inCourseCategory.value) params.set('category', inCourseCategory.value)
    if (inCourseSemester.value) params.set('semester', inCourseSemester.value)

    const resp = await $fetch<{ code: number; data?: any[]; total?: number }>(`${apiBase}/api/v1/materials?${params.toString()}`)
    const items = resp.code === 0 && Array.isArray(resp.data) ? resp.data : []
    materials.value = items
    total.value = resp.code === 0 && typeof resp.total === 'number' ? resp.total : items.length
  } catch (e) {
    console.error('[course] fetchCourseMaterials failed page=%d:', page, e)
    if (page === 1) materials.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function searchInCourse() {
  currentPage.value = 1
  void fetchCourseMaterials(1)
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  fetchCourseMaterials(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
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
    const [courseResp] = await Promise.all([
      $fetch<{ code: number; data: any }>(`${apiBase}/api/v1/courses/${route.params.id}`),
    ])
    if (courseResp.code === 0) {
      course.value = courseResp.data
      saveRecentCourse()
    }
  } catch { /* noop */ }
  await fetchCourseMaterials(1)
})
</script>
