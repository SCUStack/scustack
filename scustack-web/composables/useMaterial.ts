import type { MaterialItem, MaterialVersion, CollectionItem } from '~/types/api'

/**
 * Composable for material detail page — encapsulates data fetching, rating,
 * bookmark, collection, report, correction, and version upload logic.
 */
export function useMaterial(materialId: Ref<string>) {
  const { apiBase } = useRuntimeConfig().public
  const auth = useAuthStore()
  const toast = useToast()

  // ── State ─────────────────────────────────────────────────────────────
  const material = ref<MaterialItem | null>(null)
  const versions = ref<MaterialVersion[]>([])
  const related = ref<MaterialItem[]>([])
  const courseName = ref('')
  const loading = ref(true)
  const isBookmarked = ref(false)

  // ── Computed ──────────────────────────────────────────────────────────

  const downloadUrl = computed(() => `${apiBase}/api/v1/materials/${materialId.value}/download`)
  const previewUrl = computed(() => `${apiBase}/api/v1/materials/${materialId.value}/download`)

  const canUploadNewVersion = computed(() => {
    if (!auth.isLoggedIn || !material.value) return false
    if (material.value.source_type !== 'hosted') return false
    const isOwner = auth.user?.id === material.value.contributor_id
    const isPrivileged = auth.user?.role === 'maintainer' || auth.user?.role === 'admin'
    return isOwner || isPrivileged
  })

  const textExtensions = new Set([
    'txt', 'md', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'hpp', 'css', 'html', 'xml',
    'json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'sh', 'bash', 'sql', 'r', 'go', 'rs',
    'swift', 'kt', 'rb', 'php', 'pl', 'lua', 'vue', 'svelte', 'jsx', 'tsx', 'csv', 'log', 'tex', 'sty',
  ])

  const isTextFormat = computed(() => {
    if (!material.value?.format) return false
    return textExtensions.has(material.value.format.toLowerCase())
  })

  const contributorBadgeIcons: Record<string, string> = {
    first_upload: 'Upload', prolific_10: 'Layers', prolific_50: 'Layers', prolific_100: 'Layers',
    popular_100: 'TrendingUp', popular_1000: 'TrendingUp', popular_10000: 'TrendingUp',
    selfless: 'HeartHandshake', college_contributor: 'GraduationCap',
    continuous_3: 'CalendarCheck', wish_fulfiller: 'Sparkles',
  }

  const LEVELED_BADGE_FAMILIES: Record<string, string[]> = {
    prolific: ['prolific_10', 'prolific_50', 'prolific_100'],
    popular: ['popular_100', 'popular_1000', 'popular_10000'],
  }

  const contributorBadges = computed(() => {
    const badges = material.value?.contributor?.badges || []
    const badgeTypes = new Set(badges.map((b: { badge_type: string }) => b.badge_type))
    const seen = new Set<string>()
    return badges.filter((b: { badge_type: string }) => {
      const familyKey = Object.keys(LEVELED_BADGE_FAMILIES).find(f =>
        LEVELED_BADGE_FAMILIES[f].includes(b.badge_type),
      )
      if (!familyKey) return true
      if (seen.has(familyKey)) return false
      seen.add(familyKey)
      const familyLevels = LEVELED_BADGE_FAMILIES[familyKey]
      const highestEarned = familyLevels.findLast(t => badgeTypes.has(t)) || b.badge_type
      return b.badge_type === highestEarned
    })
  })

  // ── Data fetching ────────────────────────────────────────────────────

  interface RecentItem { id: string; type: string; title: string; url: string; time: string }

  function saveRecentView() {
    if (!material.value) return
    try {
      const raw = localStorage.getItem('scustack_recent')
      const list: RecentItem[] = raw ? JSON.parse(raw) : []
      const filtered = list.filter((i) => i.id !== material.value!.id)
      filtered.unshift({
        id: material.value.id, type: 'material',
        title: material.value.title, url: `/material/${material.value.id}`,
        time: new Date().toLocaleDateString('zh-CN'),
      })
      localStorage.setItem('scustack_recent', JSON.stringify(filtered.slice(0, 20)))
    } catch { /* ignore */ }
  }

  async function fetchMaterial(retryAttempt = 0) {
    const id = materialId.value
    if (retryAttempt === 0) loading.value = true
    const MAX_RETRIES = 2

    const fetchWithRetry = async <T>(url: string): Promise<{ code: number; data: T }> => {
      try {
        return await $fetch<{ code: number; data: T }>(url)
      } catch (e: unknown) {
        const err = e as { status?: number }
        if (err.status === 429 && retryAttempt < MAX_RETRIES) {
          await new Promise(r => setTimeout(r, 800 * (retryAttempt + 1)))
          return { code: 0, data: [] as unknown as T }
        }
        return { code: 0, data: [] as unknown as T }
      }
    }

    try {
      const resp = await $fetch<{ code: number; data: MaterialItem | null }>(`${apiBase}/api/v1/materials/${id}`)
      if (resp.code === 0) {
        material.value = resp.data
        saveRecentView()
      } else if (resp.code === 42900 && retryAttempt < MAX_RETRIES) {
        await new Promise(r => setTimeout(r, 1000 * (retryAttempt + 1)))
        loading.value = false
        return fetchMaterial(retryAttempt + 1)
      }

      const [versionResp, relatedResp, courseResp] = await Promise.all([
        fetchWithRetry<MaterialVersion[]>(`${apiBase}/api/v1/materials/${id}/versions`),
        fetchWithRetry<MaterialItem[]>(`${apiBase}/api/v1/materials/${id}/related`),
        resp.data?.course_id
          ? fetchWithRetry<{ name: string }>(`${apiBase}/api/v1/courses/${resp.data.course_id}`)
          : Promise.resolve({ code: 0, data: null as unknown as { name: string } }),
      ])
      if (versionResp.code === 0 && Array.isArray(versionResp.data)) versions.value = versionResp.data
      if (relatedResp.code === 0 && Array.isArray(relatedResp.data)) related.value = relatedResp.data
      if (courseResp.code === 0 && courseResp.data) courseName.value = courseResp.data.name
    } catch { /* fallback: keep existing data if any */ }
    loading.value = false
  }

  // ── Actions ──────────────────────────────────────────────────────────

  async function toggleBookmark() {
    if (!auth.isLoggedIn) { auth.openLogin(); return }
    const { toggleBookmark: doToggle } = useAuth()
    try {
      await doToggle(undefined, materialId.value)
      isBookmarked.value = !isBookmarked.value
      toast.success(isBookmarked.value ? '已收藏' : '已取消收藏')
    } catch { /* noop */ }
  }

  async function submitReport(reason: string, description: string) {
    const resp = await $fetch<{ code: number; message: string }>(
      `${apiBase}/api/v1/materials/${materialId.value}/reports`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason, description }),
      },
    )
    if (resp.code !== 0) throw new Error(resp.message || '提交失败')
  }

  async function submitCorrection(fieldName: string, currentValue: string, suggestedValue: string) {
    const resp = await $fetch<{ code: number; message: string }>(
      `${apiBase}/api/v1/materials/${materialId.value}/corrections`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field_name: fieldName, current_value: currentValue, suggested_value: suggestedValue }),
      },
    )
    if (resp.code !== 0) throw new Error(resp.message)
  }

  async function fetchCollections(): Promise<CollectionItem[]> {
    const resp = await $fetch<{ code: number; data: CollectionItem[] }>(`${apiBase}/api/v1/collections`, { credentials: 'include' })
    return resp.code === 0 ? resp.data : []
  }

  async function addToCollection(collectionId: string) {
    const resp = await $fetch<{ code: number; message: string }>(
      `${apiBase}/api/v1/collections/${collectionId}/items`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ material_id: materialId.value }),
      },
    )
    if (resp.code !== 0) throw new Error(resp.message)
  }

  async function createCollection(title: string): Promise<string> {
    const resp = await $fetch<{ code: number; data: { id: string } }>(
      `${apiBase}/api/v1/collections`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      },
    )
    if (resp.code !== 0) throw new Error('创建合辑失败')
    return resp.data.id
  }

  async function submitNewVersion(file: File, changeNote: string): Promise<void> {
    const hashBuffer = await crypto.subtle.digest('SHA-256', await file.arrayBuffer())
    const fileHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0')).join('')

    const tokenResp = await $fetch<{ code: number; message: string; data: { upload_url: string; storage_key: string } }>(
      `${apiBase}/api/v1/upload/token`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: file.name, content_type: file.type || 'application/octet-stream', file_size: file.size }),
      },
    )
    if (tokenResp.code !== 0) throw new Error(tokenResp.message || '获取上传凭证失败')

    await $fetch(tokenResp.data.upload_url, { method: 'PUT', body: file })

    const resp = await $fetch<{ code: number; data: MaterialVersion | null; message: string }>(
      `${apiBase}/api/v1/materials/${materialId.value}/versions`,
      {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storage_key: tokenResp.data.storage_key,
          file_hash: fileHash, file_size: file.size,
          change_note: changeNote || undefined,
        }),
      },
    )
    if (resp.code !== 0) throw new Error(resp.message || '版本上传失败')

    // Refresh material and versions
    const [materialResp, versionResp] = await Promise.all([
      $fetch<{ code: number; data: MaterialItem | null }>(`${apiBase}/api/v1/materials/${materialId.value}`),
      $fetch<{ code: number; data: MaterialVersion[] }>(`${apiBase}/api/v1/materials/${materialId.value}/versions`),
    ])
    if (materialResp.code === 0) material.value = materialResp.data
    if (versionResp.code === 0) versions.value = versionResp.data
  }

  return {
    material, versions, related, courseName, loading, isBookmarked,
    downloadUrl, previewUrl, canUploadNewVersion, isTextFormat,
    contributorBadges, contributorBadgeIcons,
    fetchMaterial, toggleBookmark, submitReport, submitCorrection,
    fetchCollections, addToCollection, createCollection, submitNewVersion,
  }
}
