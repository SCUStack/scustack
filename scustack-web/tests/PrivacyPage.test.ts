import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('privacy page defaults', () => {
  it('defaults public contributions to the user nickname', () => {
    const source = readFileSync(resolve(__dirname, '../pages/user/privacy.vue'), 'utf-8')
    expect(source).toContain("ref<'anonymous' | 'nickname'>('nickname')")
  })
})
