export const DEFAULT_AVATARS = Array.from(
  { length: 6 },
  (_, index) => `/avatars/avatar-${index + 1}.png`,
)

export function getDefaultAvatar(seed: string): string {
  let hash = 0
  for (const character of seed) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0
  }
  return DEFAULT_AVATARS[hash % DEFAULT_AVATARS.length]
}
