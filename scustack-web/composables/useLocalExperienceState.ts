export interface RecentItem {
  id: string
  type: 'material' | 'course'
  title: string
  url: string
  time: string
}

export interface UploadDraft {
  title: string
  collegeId: string
  courseId: string
  category: string
  semester: string
  teacher: string
  sourceType: 'hosted' | 'external'
  externalUrl: string
  description: string
  fulfillWishId: string
}

export const localExperienceStateRegistry = {
  recentViews: {
    storageKey: 'scustack_recent',
    kind: 'local_experience',
    description: 'Recently viewed courses and materials for convenience-only profile/history surfaces.',
  },
  searchHistory: {
    storageKey: 'scustack_search_history',
    kind: 'local_experience',
    description: 'Per-browser search history used only to speed up repeat searches.',
  },
  uploadDraft: {
    storageKey: 'uploadDraft',
    kind: 'local_experience',
    description: 'Unsubmitted upload form draft for recovery after refresh or accidental navigation.',
  },
  dismissedAnnouncement: {
    storageKeyPrefix: 'scustack_dismissed:',
    kind: 'local_experience',
    description: 'Per-day dismissal state for already seen announcements in the current browser.',
  },
} as const

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Ignore unavailable or full local storage and keep UX functional.
  }
}

function removeKey(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    // Ignore unavailable local storage and keep UX functional.
  }
}

export function loadRecentViews(): RecentItem[] {
  return readJson(localExperienceStateRegistry.recentViews.storageKey, [])
}

export function saveRecentView(item: RecentItem) {
  const filtered = loadRecentViews().filter(existing => existing.id !== item.id)
  filtered.unshift(item)
  writeJson(localExperienceStateRegistry.recentViews.storageKey, filtered.slice(0, 20))
}

export function loadSearchHistory(): string[] {
  return readJson(localExperienceStateRegistry.searchHistory.storageKey, [])
}

export function saveSearchHistory(history: string[]) {
  writeJson(localExperienceStateRegistry.searchHistory.storageKey, history)
}

export function clearSearchHistory() {
  removeKey(localExperienceStateRegistry.searchHistory.storageKey)
}

export function loadUploadDraft(): UploadDraft | null {
  return readJson<UploadDraft | null>(localExperienceStateRegistry.uploadDraft.storageKey, null)
}

export function saveUploadDraft(draft: UploadDraft) {
  writeJson(localExperienceStateRegistry.uploadDraft.storageKey, draft)
}

export function clearUploadDraft() {
  removeKey(localExperienceStateRegistry.uploadDraft.storageKey)
}

function dismissedAnnouncementKey(id: string) {
  return `${localExperienceStateRegistry.dismissedAnnouncement.storageKeyPrefix}${id}`
}

export function markAnnouncementDismissed(id: string, dayToken: string) {
  try {
    localStorage.setItem(dismissedAnnouncementKey(id), dayToken)
  } catch {
    // Ignore unavailable local storage and keep UX functional.
  }
}

export function isAnnouncementDismissed(id: string, dayToken: string): boolean {
  try {
    return localStorage.getItem(dismissedAnnouncementKey(id)) === dayToken
  } catch {
    return false
  }
}
