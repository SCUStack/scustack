import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const mobileCard = readFileSync(new URL('../components/mobile/MaterialWaterfallCard.vue', import.meta.url), 'utf8')
const desktopCard = readFileSync(new URL('../components/material/MaterialCard.vue', import.meta.url), 'utf8')

describe('material card layout', () => {
  it('uses a stable image proportion on mobile instead of per-title variation', () => {
    expect(mobileCard).toContain('aspect-[4/3] w-full object-cover')
    expect(mobileCard).not.toContain('const imageAspect = computed')
    expect(mobileCard).not.toContain('const ratios =')
  })

  it('keeps title and engagement metadata as the shared information priority', () => {
    for (const card of [mobileCard, desktopCard]) {
      expect(card).toContain('line-clamp-2 text-sm font-semibold')
      expect(card).toContain('ratingText')
      expect(card).toContain('download_count')
    }
  })
})
