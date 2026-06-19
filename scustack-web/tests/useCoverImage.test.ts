import { describe, expect, it } from 'vitest'

import { coverTagsData } from '../data/coverRules'
import { resolveCoverSync } from '../composables/useCoverImage'

describe('useCoverImage rules', () => {
  it('uses the shared subject alias rules when matching covers', () => {
    const cover = resolveCoverSync(
      { id: '1', title: 'C++程序设计期末试卷', category: '考试资料' },
      coverTagsData,
    )
    expect(cover).toContain('/covers/考试资料/')
    expect(cover).toContain('exam_cs.svg')
  })

  it('infers category from title when the upstream category is missing', () => {
    const cover = resolveCoverSync(
      { id: '2', title: '数据库系统复习提纲重点总结', category: '' },
      coverTagsData,
    )
    expect(cover).toContain('/covers/复习提纲/')
  })
})
