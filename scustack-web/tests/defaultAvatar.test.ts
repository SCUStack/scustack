import { describe, expect, it } from 'vitest'
import { getDefaultAvatar } from '../utils/defaultAvatar'

describe('getDefaultAvatar', () => {
  it('returns a stable local avatar for the same user', () => {
    expect(getDefaultAvatar('user-a')).toBe(getDefaultAvatar('user-a'))
    expect(getDefaultAvatar('user-a')).toMatch(/^\/avatars\/avatar-[1-6]\.png$/)
  })

  it('distributes different user IDs across the local avatar set', () => {
    const avatars = new Set(Array.from({ length: 20 }, (_, index) => getDefaultAvatar(`user-${index}`)))
    expect(avatars.size).toBeGreaterThan(1)
  })
})
