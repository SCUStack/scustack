export const materialCategories = [
  '课堂笔记',
  '考试资料',
  '复习提纲',
  '教材',
  '习题集',
  '实验报告',
  '历年真题',
  '课件讲义',
  '考研专区',
] as const

export const materialSemesters = [
  '2026-2027-1',
  '2025-2026-2',
  '2025-2026-1',
  '2024-2025-2',
  '2024-2025-1',
] as const

export const sourceTypeOptions = [
  { value: 'hosted', label: '托管文件' },
  { value: 'external', label: '外部链接' },
] as const

export const trustStatusConfig = {
  maintainer_picked: { label: '维护者精选', icon: 'ShieldCheck', class: 'bg-amber-50 text-amber-600' },
  community_verified: { label: '社区验证', icon: 'Users', class: 'bg-emerald-50 text-emerald-600' },
  unverified: { label: '未验证', icon: 'Circle', class: 'bg-slate-100 text-slate-400' },
  doubtful: { label: '存疑', icon: 'AlertTriangle', class: 'bg-red-50 text-red-600' },
} as const

export const searchSortOptions = [
  { key: 'relevance', label: '相关度' },
  { key: 'newest', label: '最新' },
  { key: 'downloads', label: '最多下载' },
  { key: 'rating', label: '最高评分' },
] as const

export const categoryOptions = materialCategories.map(value => ({ value, label: value }))
export const semesterOptions = materialSemesters.map(value => ({ value, label: value }))
export const trustStatusOptions = Object.entries(trustStatusConfig).map(([value, config]) => ({
  value,
  label: config.label,
}))

export const searchFilterGroupLabels: Record<string, string> = {
  category: '分类',
  semester: '学期',
  source_type: '来源',
  format: '格式',
  trust_status: '信任状态',
  college_id: '学院',
}

export const searchFilterGroups = [
  { key: 'category', label: '资料分类', options: categoryOptions },
  { key: 'semester', label: '学期', options: semesterOptions },
  { key: 'trust_status', label: '信任状态', options: trustStatusOptions },
  { key: 'source_type', label: '来源', options: sourceTypeOptions },
] as const

export const businessLabelMaps: Record<string, Record<string, string>> = {
  category: Object.fromEntries(categoryOptions.map(option => [option.value, option.label])),
  semester: Object.fromEntries(semesterOptions.map(option => [option.value, option.label])),
  source_type: Object.fromEntries(sourceTypeOptions.map(option => [option.value, option.label])),
  trust_status: Object.fromEntries(trustStatusOptions.map(option => [option.value, option.label])),
  format: {},
}

export function getBusinessLabel(value: string): string {
  for (const map of Object.values(businessLabelMaps)) {
    if (map[value]) return map[value]
  }
  return value
}

export type MaterialCategory = (typeof materialCategories)[number]
export type MaterialSemester = (typeof materialSemesters)[number]
export type MaterialSourceType = (typeof sourceTypeOptions)[number]['value']
export type TrustStatus = keyof typeof trustStatusConfig
export type SearchSort = (typeof searchSortOptions)[number]['key']
