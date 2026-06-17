import type { Course } from '~/types/api'

/**
 * Course store — selected college, course list cache, filter state.
 * Centralizes course-related state shared across upload, search, and course pages.
 */
export const useCourseStore = defineStore('course', () => {
  const { apiBase } = useRuntimeConfig().public

  const selectedCollegeId = ref<string>('')
  const courses = ref<Course[]>([])
  const courseCache = ref<Map<string, Course[]>>(new Map())
  const filters = reactive({
    collegeId: '',
    category: '',
    semester: '',
    format: '',
  })

  const hasCourses = computed(() => courses.value.length > 0)
  const selectedCollegeName = ref('')

  async function fetchCourses(collegeId: string) {
    if (!collegeId) {
      courses.value = []
      return
    }

    if (courseCache.value.has(collegeId)) {
      courses.value = courseCache.value.get(collegeId)!
      return
    }

    try {
      const resp = await $fetch<{ code: number; data: Course[] }>(
        `${apiBase}/api/v1/courses?college_id=${collegeId}`,
      )
      if (resp.code === 0) {
        courseCache.value.set(collegeId, resp.data)
        courses.value = resp.data
      }
    } catch {
      courses.value = []
    }
  }

  function selectCollege(collegeId: string, name?: string) {
    selectedCollegeId.value = collegeId
    selectedCollegeName.value = name || ''
    filters.collegeId = collegeId
    fetchCourses(collegeId)
  }

  function setFilter(key: keyof typeof filters, value: string) {
    filters[key] = value
  }

  function clearFilters() {
    filters.category = ''
    filters.semester = ''
    filters.format = ''
  }

  function $reset() {
    selectedCollegeId.value = ''
    courses.value = []
    courseCache.value = new Map()
    filters.collegeId = ''
    filters.category = ''
    filters.semester = ''
    filters.format = ''
    selectedCollegeName.value = ''
  }

  return {
    selectedCollegeId, courses, courseCache, filters,
    hasCourses, selectedCollegeName,
    fetchCourses, selectCollege, setFilter, clearFilters, $reset,
  }
})
