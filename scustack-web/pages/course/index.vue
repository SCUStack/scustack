<template>
  <div>
    <!-- Desktop -->
    <div class="hidden lg:block">
      <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '全部课程' }]" />
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 class="text-2xl font-semibold text-slate-900 mb-1">全部课程</h1>
        <p class="text-sm text-slate-500 mb-6">共 {{ courseTotal }} 门课程</p>

        <div v-if="courseLoading" class="space-y-3">
          <SkeletonList :count="8" />
        </div>

        <div v-else-if="courses.length > 0">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            <NuxtLink
              v-for="c in courses"
              :key="c.id"
              :to="`/course/${c.id}`"
              class="block p-4 border border-slate-200 rounded-lg hover:shadow-sm hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer bg-white"
            >
              <h3 class="text-base font-medium text-slate-800 line-clamp-1">{{ c.name }}</h3>
              <p class="text-xs text-slate-400 mt-1">
                {{ c.college_name || '' }}
                <span v-if="c.category && c.category !== '未分类'"> · {{ c.category }}</span>
                <span v-if="c.credit"> · {{ c.credit }} 学分</span>
              </p>
              <p v-if="c.material_count" class="text-xs text-slate-400 mt-1">{{ c.material_count }} 份资料</p>
            </NuxtLink>
          </div>

          <div v-if="courseTotalPages > 1" class="flex items-center justify-center gap-1 pb-8">
            <button
              :disabled="coursePage <= 1"
              class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
              @click="goToCoursePage(coursePage - 1)"
            >
              上一页
            </button>
            <button
              v-for="p in coursePageNumbers"
              :key="p"
              :class="[
                'px-3 py-1.5 text-sm border rounded-md cursor-pointer transition-colors duration-150',
                p === coursePage ? 'bg-primary-500 text-white border-primary-500' : 'border-slate-200 hover:bg-slate-50 text-slate-600',
              ]"
              @click="goToCoursePage(p)"
            >
              {{ p }}
            </button>
            <button
              :disabled="coursePage >= courseTotalPages"
              class="px-3 py-1.5 text-sm border border-slate-200 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer transition-colors duration-150"
              @click="goToCoursePage(coursePage + 1)"
            >
              下一页
            </button>
          </div>
        </div>

        <EmptyState
          v-else
          icon="BookOpen"
          title="暂无课程"
          description="当前还没有收录课程"
        />
      </div>
    </div>

    <!-- Mobile -->
    <div class="lg:hidden px-4 pt-4 pb-4">
      <h1 class="text-lg font-semibold text-slate-900 mb-4">全部课程</h1>

      <div v-if="courseLoading" class="space-y-3">
        <SkeletonList :count="6" />
      </div>

      <div v-else-if="courses.length > 0" class="flex gap-3">
        <div class="flex-1 space-y-3">
          <NuxtLink
            v-for="(c, idx) in courseLeftCol"
            :key="c.id"
            :to="`/course/${c.id}`"
            class="block p-4 border border-slate-200 rounded-xl hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer bg-white active:scale-[0.98] animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50}ms` }"
          >
            <h3 class="text-sm font-medium text-slate-800 line-clamp-1">{{ c.name }}</h3>
            <p class="text-xs text-slate-400 mt-1">{{ c.college_name || '' }}</p>
            <p v-if="c.material_count" class="text-xs text-slate-400 mt-0.5">{{ c.material_count }} 份资料</p>
          </NuxtLink>
        </div>
        <div class="flex-1 space-y-3">
          <NuxtLink
            v-for="(c, idx) in courseRightCol"
            :key="c.id"
            :to="`/course/${c.id}`"
            class="block p-4 border border-slate-200 rounded-xl hover:border-primary-200 transition-all duration-200 no-underline cursor-pointer bg-white active:scale-[0.98] animate-card-enter"
            :style="{ animationDelay: `${(idx % 6) * 50 + 25}ms` }"
          >
            <h3 class="text-sm font-medium text-slate-800 line-clamp-1">{{ c.name }}</h3>
            <p class="text-xs text-slate-400 mt-1">{{ c.college_name || '' }}</p>
            <p v-if="c.material_count" class="text-xs text-slate-400 mt-0.5">{{ c.material_count }} 份资料</p>
          </NuxtLink>
        </div>
      </div>

      <EmptyState
        v-else
        icon="BookOpen"
        title="暂无课程"
        description="当前还没有收录课程"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ ssr: true })

const { apiBase } = useRuntimeConfig().public

const courses = ref<any[]>([])
const courseTotal = ref(0)
const coursePage = ref(1)
const courseLoading = ref(true)
const PAGE_SIZE = 20

const courseTotalPages = computed(() => Math.ceil(courseTotal.value / PAGE_SIZE) || 1)

const courseLeftCol = computed(() => courses.value.filter((_, i) => i % 2 === 0))
const courseRightCol = computed(() => courses.value.filter((_, i) => i % 2 === 1))

const coursePageNumbers = computed(() => {
  const pages: number[] = []
  const total = courseTotalPages.value
  const current = coursePage.value
  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(total, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

async function fetchCourses(page: number) {
  courseLoading.value = true
  try {
    const resp = await $fetch<{ code: number; data: { courses: any[]; total: number } }>(
      `${apiBase}/api/v1/courses?page=${page}&page_size=${PAGE_SIZE}`,
    )
    if (resp.code === 0) {
      courses.value = resp.data.courses
      courseTotal.value = resp.data.total
      coursePage.value = page
    }
  } catch { /* noop */ }
  courseLoading.value = false
}

function goToCoursePage(page: number) {
  if (page < 1 || page > courseTotalPages.value) return
  fetchCourses(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  fetchCourses(1)
})
</script>
