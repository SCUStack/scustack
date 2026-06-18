import type { UserProfile, MaterialItem, NotificationList, PaginatedItems, Course } from '~/types/api'

export function useAuth() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  async function sendCode(phone: string) {
    return $fetch<{ code: number; message: string }>(`${base}/api/v1/auth/sms/send`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
    })
  }

  async function verifyCode(phone: string, code: string) {
    return $fetch<{ code: number; data: null; message: string }>(
      `${base}/api/v1/auth/sms/verify`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      },
    )
  }

  async function refresh() {
    return $fetch<{ code: number; data: null; message: string }>(
      `${base}/api/v1/auth/refresh`,
      {
        method: 'POST',
        credentials: 'include',
      },
    )
  }

  async function logout() {
    return $fetch<{ code: number; message: string }>(`${base}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    })
  }

  async function getMe() {
    return $fetch<{ code: number; data: { id: string; nickname: string; role: string; avatar_url: string | null; trust_score: number; public_display_name: string | null; created_at: string } | null; message: string }>(
      `${base}/api/v1/me`,
      { credentials: 'include' },
    )
  }

  async function updateProfile(body: { nickname?: string; avatar_url?: string; public_display_name?: string }) {
    return $fetch<{ code: number; data: UserProfile | null; message: string }>(
      `${base}/api/v1/me`,
      {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      },
    )
  }

  async function getContributions(limit = 20, offset = 0) {
    return $fetch<{ code: number; data: PaginatedItems<MaterialItem>; message: string }>(
      `${base}/api/v1/me/contributions?limit=${limit}&offset=${offset}`,
      { credentials: 'include' },
    )
  }

  async function toggleBookmark(courseId?: string, materialId?: string) {
    return $fetch<{ code: number; data: { action: string; bookmark_id: string }; message: string }>(
      `${base}/api/v1/bookmarks`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_id: courseId || null, material_id: materialId || null }),
      },
    )
  }

  async function getBookmarks(type: 'course' | 'material' = 'course') {
    return $fetch<{ code: number; data: (Course | MaterialItem)[]; message: string }>(
      `${base}/api/v1/bookmarks?type=${type}`,
      { credentials: 'include' },
    )
  }

  async function getNotifications(limit = 20, offset = 0) {
    return $fetch<{ code: number; data: NotificationList; message: string }>(
      `${base}/api/v1/me/notifications?limit=${limit}&offset=${offset}`,
      { credentials: 'include' },
    )
  }

  async function getUnreadCount() {
    return $fetch<{ code: number; data: { count: number }; message: string }>(
      `${base}/api/v1/me/unread-count`,
      { credentials: 'include' },
    )
  }

  async function markNotificationRead(notificationId: string) {
    return $fetch<{ code: number; message: string }>(
      `${base}/api/v1/me/notifications/${notificationId}/read`,
      { method: 'PATCH', credentials: 'include' },
    )
  }

  async function markAllNotificationsRead() {
    return $fetch<{ code: number; message: string }>(
      `${base}/api/v1/me/notifications/read-all`,
      { method: 'PATCH', credentials: 'include' },
    )
  }

  async function getPrivacy() {
    return $fetch<{ code: number; data: { public_display_name: string }; message: string }>(
      `${base}/api/v1/me/privacy`,
      { credentials: 'include' },
    )
  }

  async function updatePrivacy(publicDisplayName: string) {
    return $fetch<{ code: number; message: string }>(
      `${base}/api/v1/me/privacy`,
      {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ public_display_name: publicDisplayName }),
      },
    )
  }

  async function deactivateAccount() {
    return $fetch<{ code: number; message: string }>(
      `${base}/api/v1/me/deactivate`,
      { method: 'POST', credentials: 'include' },
    )
  }

  async function getSessions() {
    return $fetch<{ code: number; data: { id: string; created_at: string; expires_at: string }[]; message: string }>(
      `${base}/api/v1/auth/sessions`,
      { credentials: 'include' },
    )
  }

  async function deleteSession(tokenId: string) {
    return $fetch<{ code: number; message: string }>(
      `${base}/api/v1/auth/sessions/${tokenId}`,
      { method: 'DELETE', credentials: 'include' },
    )
  }

  async function loginWithPassword(phone: string, password: string) {
    return $fetch<{ code: number; data: null; message: string }>(
      `${base}/api/v1/auth/login`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      },
    )
  }

  async function registerWithPassword(phone: string, password: string, confirmPassword: string) {
    return $fetch<{ code: number; data: null; message: string }>(
      `${base}/api/v1/auth/register`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password, confirm_password: confirmPassword }),
      },
    )
  }

  async function getWechatUrl() {
    return $fetch<{ code: number; data: { url: string }; message: string }>(
      `${base}/api/v1/auth/wechat/url`,
      { credentials: 'include' },
    )
  }

  async function getBadges() {
    return $fetch<{ code: number; data: { badges: { id: string; badge_type: string; label: string; description: string; color: string; awarded_at: string }[]; total: number }; message: string }>(
      `${base}/api/v1/me/badges`,
      { credentials: 'include' },
    )
  }

  return {
    sendCode, verifyCode, refresh, logout, getMe, updateProfile,
    getContributions, toggleBookmark, getBookmarks, getBadges,
    getNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead,
    getPrivacy, updatePrivacy, deactivateAccount,
    getSessions, deleteSession, getWechatUrl,
    loginWithPassword, registerWithPassword,
  }
}
