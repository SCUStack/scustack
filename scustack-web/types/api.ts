/** Core API response types shared across the frontend */

export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

export interface PaginatedItems<T> {
  items: T[]
  total: number
}

// ── User ──
export interface UserProfile {
  id: string
  nickname: string
  phone?: string
  avatar_url?: string
  role: 'visitor' | 'student' | 'contributor' | 'maintainer' | 'admin'
  trust_score: number
  created_at: string
}

export interface UserBadge {
  badge_type: string
  label: string
  description: string
  color: string
  earned_at: string
}

// ── College & Course ──
export interface College {
  id: string
  name: string
  material_count?: number
}

export interface Course {
  id: string
  name: string
  college_id: string
  college_name?: string
  aliases?: string[]
  material_count?: number
}

// ── Material ──
export interface MaterialContributor {
  nickname: string
  avatar_url?: string
  trust_score: number
  badges?: UserBadge[]
}

export interface MaterialItem {
  id: string
  title: string
  course_id: string
  course_name?: string
  category: string
  semester: string
  format: string
  file_size?: number
  source_type: 'hosted' | 'external'
  external_url?: string
  description?: string
  trust_status: 'unverified' | 'community_verified' | 'maintainer_picked' | 'doubtful'
  average_rating: number
  rating_avg?: number
  rating_count: number
  rating_distribution?: Record<number, number>
  download_count: number
  contributor_id?: string
  contributor?: MaterialContributor
  created_at: string
  updated_at: string
  file_hash?: string
  thumbnail_url?: string
  pinned?: boolean
  parts?: Array<{ id: string; title: string }>
  teacher?: string
}

export interface MaterialVersion {
  id: string
  version_number: number
  change_note?: string
  file_size?: number
  storage_key: string
  created_at: string
}

export interface DiffResponse {
  version_id: string
  version_number: number
  change_note?: string
  diff: string[] | null
  truncated?: boolean
  message?: string
}

// ── Notification ──
export interface NotificationItem {
  id: string
  title: string
  body?: string
  is_read: boolean
  resource_type?: string
  resource_id?: string
  created_at: string
}

export interface NotificationList {
  items: NotificationItem[]
  unread_count: number
}

// ── Collection ──
export interface CollectionItem {
  id: string
  name: string
  title?: string
  description?: string
  material_count: number
  is_public: boolean
  created_at: string
}

// ── Comment ──
export interface CommentItem {
  id: string
  content: string
  user: { nickname: string; avatar_url?: string }
  parent_id?: string
  created_at: string
}

// ── Wish ──
export interface WishItem {
  id: string
  course_id: string
  description: string
  vote_count: number
  has_voted: boolean
  fulfilled: boolean
  created_at: string
}

// ── Rating ──
export interface RatingDistribution {
  [key: number]: number
}

// ── Search ──
export interface SearchResult {
  items: MaterialItem[]
  total: number
}

export interface SearchSuggestion {
  value: string
  count: number
}

// ── Homepage ──
export interface CalendarEvent {
  id: string
  date: string
  title: string
  description?: string
  tags?: string[]
}

export interface HomepageData {
  banners: Array<{ title: string; subtitle: string; image_url: string; link: string }>
  calendar_items: CalendarEvent[]
  recent_items: MaterialItem[]
  hot_courses: Course[]
  colleges: College[]
}

// ── Upload ──
export interface UploadToken {
  storage_key: string
  presigned_url: string
  expires_in: number
}
