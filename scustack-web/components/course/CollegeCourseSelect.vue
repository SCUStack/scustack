<template>
  <div class="flex gap-3">
    <div class="flex-1">
      <label class="block text-sm text-slate-600 mb-1">{{ collegeLabel }}</label>
      <select
        v-model="selectedCollegeId"
        :aria-label="collegeLabel"
        class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
        @change="onCollegeChange"
      >
        <option value="">选择学院</option>
        <option v-for="c in colleges" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>
    <div class="flex-1">
      <label class="block text-sm text-slate-600 mb-1">{{ courseLabel }}</label>
      <select
        v-model="selectedCourseId"
        :aria-label="courseLabel"
        class="w-full h-10 px-3 border border-slate-200 rounded-md text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 disabled:bg-slate-50 disabled:text-slate-400"
        :disabled="!selectedCollegeId"
        @change="onCourseChange"
      >
        <option value="">选择课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  collegeLabel?: string
  courseLabel?: string
}>(), {
  collegeLabel: '所属学院',
  courseLabel: '所属课程',
})

const emit = defineEmits<{
  'update:collegeId': [id: string]
  'update:courseId': [id: string]
}>()

const selectedCollegeId = ref('')
const selectedCourseId = ref('')
const colleges = ref<{ id: string; name: string }[]>([])
const courses = ref<{ id: string; name: string }[]>([])

const { apiBase } = useRuntimeConfig().public

onMounted(async () => {
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(`${apiBase}/api/v1/colleges`)
  if (resp.code === 0) colleges.value = resp.data
})

async function onCollegeChange() {
  selectedCourseId.value = ''
  emit('update:collegeId', selectedCollegeId.value)
  emit('update:courseId', '')
  if (!selectedCollegeId.value) {
    courses.value = []
    return
  }
  const resp = await $fetch<{ code: number; data: { id: string; name: string }[] }>(
    `${apiBase}/api/v1/courses?college_id=${selectedCollegeId.value}`,
  )
  if (resp.code === 0) courses.value = resp.data
}

function onCourseChange() {
  emit('update:courseId', selectedCourseId.value)
}
</script>
