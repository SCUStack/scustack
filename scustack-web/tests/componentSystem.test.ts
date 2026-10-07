import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const image = readFileSync(resolve(__dirname, '../components/common/AppImage.vue'), 'utf8')
const desktopCard = readFileSync(resolve(__dirname, '../components/material/MaterialCard.vue'), 'utf8')
const mobileCard = readFileSync(resolve(__dirname, '../components/mobile/MaterialWaterfallCard.vue'), 'utf8')
const home = readFileSync(resolve(__dirname, '../pages/index.vue'), 'utf8')

describe('shared component and image loading system', () => {
  it('provides one shared image component with responsive loading defaults', () => {
    expect(image).toContain('defineProps')
    expect(image).toContain("loading?: 'eager' | 'lazy'")
    expect(image).toContain("fetchpriority?: 'high' | 'low' | 'auto'")
    expect(image).toContain('decoding="async"')
    expect(image).toContain('@error="onError"')
    expect(image).toContain("emit('error', event)")
  })

  it('uses the shared image component for content and hero images', () => {
    for (const source of [desktopCard, mobileCard, home]) {
      expect(source).toContain('<AppImage')
      expect(source).not.toContain('<img')
    }
  })
})
