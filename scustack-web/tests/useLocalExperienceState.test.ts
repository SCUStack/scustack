import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('useLocalExperienceState', () => {
  const storage = new Map<string, string>()

  beforeEach(() => {
    storage.clear()
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => storage.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => { storage.set(key, value) }),
      removeItem: vi.fn((key: string) => { storage.delete(key) }),
    })
  })

  it('stores recent views as local-only convenience history', async () => {
    const { loadRecentViews, saveRecentView } = await import('../composables/useLocalExperienceState')

    saveRecentView({ id: 'a', type: 'material', title: '资料A', url: '/material/a', time: '2026/6/19' })
    saveRecentView({ id: 'b', type: 'course', title: '课程B', url: '/course/b', time: '2026/6/19' })
    saveRecentView({ id: 'a', type: 'material', title: '资料A', url: '/material/a', time: '2026/6/19' })

    expect(loadRecentViews().map(item => item.id)).toEqual(['a', 'b'])
  })

  it('loads and clears upload drafts without treating them as backend truth', async () => {
    const { clearUploadDraft, loadUploadDraft, saveUploadDraft } = await import('../composables/useLocalExperienceState')

    saveUploadDraft({
      title: '草稿',
      collegeId: 'c1',
      courseId: 'course1',
      category: '课堂笔记',
      semester: '2026-2027-1',
      teacher: '',
      sourceType: 'hosted',
      externalUrl: '',
      description: '',
      fulfillWishId: '',
    })
    expect(loadUploadDraft()?.title).toBe('草稿')

    clearUploadDraft()
    expect(loadUploadDraft()).toBeNull()
  })
})
