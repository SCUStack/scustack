import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('college detail page', () => {
  const source = readFileSync(resolve(__dirname, '../pages/colleges/[id].vue'), 'utf-8')

  it('loads the college and its course collection by route ID', () => {
    expect(source).toContain('`${apiBase}/api/v1/colleges/${collegeId}`')
    expect(source).toContain('`${apiBase}/api/v1/courses?college_id=${collegeId}`')
    expect(source).toContain('课程合集')
    expect(source).toContain(':to="`/course/${c.id}`"')
  })

  it('handles invalid college IDs without calling the API', () => {
    expect(source).toContain('if (!isValidCollegeId)')
    expect(source).toContain("return { college: null, courses: [], loadFailed: false }")
  })
})
