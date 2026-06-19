import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('home page data loading', () => {
  it('loads first-screen data through async data instead of onMounted refetch', () => {
    const source = readFileSync(resolve(__dirname, '../pages/index.vue'), 'utf-8')
    const mountedBlock = source.match(/onMounted\(async\s*\(\)\s*=>\s*\{([\s\S]*?)\n\}\)/)?.[1] ?? ''

    expect(source).toContain("useAsyncData('homepage-index'")
    expect(source).toContain("`${apiBase}/api/v1/homepage`")
    expect(source).toContain("`${apiBase}/api/v1/colleges`")
    expect(mountedBlock).not.toContain('`${apiBase}/api/v1/homepage`')
    expect(mountedBlock).not.toContain('`${apiBase}/api/v1/colleges`')
  })
})
