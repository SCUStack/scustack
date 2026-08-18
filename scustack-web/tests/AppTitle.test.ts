import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('application title', () => {
  it('uses the SCUStack study slogan', () => {
    const source = readFileSync(resolve(__dirname, '../app.vue'), 'utf-8')
    expect(source).toContain("titleTemplate: '川流课栈 >( ⁰▿⁰)< 好好学习天天向上 ~ SCUStack'")
  })
})
