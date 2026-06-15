<template>
  <div class="max-w-3xl mx-auto px-2 sm:px-3 lg:px-4 py-8">
    <NuxtLink to="/user/profile" class="flex items-center gap-1 text-sm text-slate-500 hover:text-primary-600 mb-4 no-underline">
      <AppIcon name="ArrowLeft" :size="14" /> 返回个人中心
    </NuxtLink>

    <h1 class="text-xl font-semibold text-slate-900 mb-6">收藏与关注</h1>

    <!-- Tab switcher -->
    <div class="flex gap-1 bg-slate-100 rounded-md p-1 mb-6 w-fit">
      <button
        :class="[
          'px-3 py-1.5 rounded text-sm font-medium cursor-pointer transition-colors duration-150',
          activeTab === 'course' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700',
        ]"
        @click="activeTab = 'course'"
      >
        关注的课程
      </button>
      <button
        :class="[
          'px-3 py-1.5 rounded text-sm font-medium cursor-pointer transition-colors duration-150',
          activeTab === 'material' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700',
        ]"
        @click="activeTab = 'material'"
      >
        收藏的资料
      </button>
    </div>

    <div v-if="loading" class="py-16">
      <SkeletonList :count="3" />
    </div>

    <!-- Courses tab -->
    <div v-else-if="activeTab === 'course'" class="space-y-3">
      <div v-if="courses.length > 0">
        <div
          v-for="item in courses"
          :key="item.bookmark_id"
          class="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-3 hover:shadow-sm transition-shadow duration-150"
        >
          <AppIcon name="BookOpen" :size="18" class="text-primary-500 shrink-0" />
          <NuxtLink :to="`/course/${item.course_id}`" class="flex-1 text-sm text-slate-800 hover:text-primary-600 no-underline line-clamp-1">
            {{ item.course_name }}
          </NuxtLink>
          <button
            class="text-xs text-slate-400 hover:text-red-500 cursor-pointer shrink-0 transition-colors duration-150"
            @click="removeBookmark(item.bookmark_id, 'course', item.course_id)"
          >
            取消关注
          </button>
        </div>
      </div>
      <EmptyState v-else icon="Bookmark" title="还没有关注课程" action-label="浏览学院课程" action-to="/colleges" />
    </div>

    <!-- Materials tab -->
    <div v-else class="space-y-3">
      <div v-if="materials.length > 0">
        <div
          v-for="item in materials"
          :key="item.bookmark_id"
          class="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow duration-150"
        >
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <NuxtLink :to="`/material/${item.material_id}`" class="text-sm font-medium text-slate-800 hover:text-primary-600 no-underline line-clamp-1">
                {{ item.title }}
              </NuxtLink>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-xs text-slate-500">{{ item.course_name }}</span>
                <span class="text-xs text-slate-300">·</span>
                <span class="text-xs text-slate-500">{{ item.category }}</span>
                <span v-if="item.format" class="text-xs text-slate-300">·</span>
                <span v-if="item.format" class="text-xs uppercase text-slate-400">{{ item.format }}</span>
              </div>
            </div>
            <button
              class="text-xs text-slate-400 hover:text-red-500 cursor-pointer shrink-0 transition-colors duration-150"
              @click="removeBookmark(item.bookmark_id, 'material', item.material_id)"
            >
              取消收藏
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="Bookmark" title="还没有收藏资料" action-label="去发现资料" action-to="/search" />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const activeTab = ref<'course' | 'material'>('course')
const courses = ref<any[]>([])
const materials = ref<any[]>([])
const loading = ref(true)

async function loadData() {
  loading.value = true
  const { getBookmarks } = useAuth()
  try {
    const [courseResp, materialResp] = await Promise.all([
      getBookmarks('course'),
      getBookmarks('material'),
    ])
    if (courseResp.code === 0) courses.value = courseResp.data
    if (materialResp.code === 0) materials.value = materialResp.data
  } catch { /* noop */ }
  loading.value = false
}

async function removeBookmark(_bookmarkId: string, type: 'course' | 'material', id: string) {
  const { toggleBookmark } = useAuth()
  const body = type === 'course' ? { courseId: id } : { materialId: id }
  await toggleBookmark(body.courseId, body.materialId)
  await loadData()
}

onMounted(loadData)
</script>
