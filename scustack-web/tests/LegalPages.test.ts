import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const privacy = readFileSync(resolve(__dirname, '../pages/privacy.vue'), 'utf-8')
const terms = readFileSync(resolve(__dirname, '../pages/terms.vue'), 'utf-8')

describe('public legal pages', () => {
  it('describes the data flows currently implemented by the website', () => {
    expect(privacy).toContain('版本：v2.0')
    expect(privacy).toContain('LFS 文件服务')
    expect(privacy).toContain('Sentry（配置启用时）')
    expect(privacy).toContain('localStorage')
    expect(privacy).toContain('csrf_token')
    expect(privacy).toContain('学校密码不保存')
  })

  it('describes the current deactivation behavior without promising unsupported choices', () => {
    expect(privacy).toContain('当前“隐私设置”中的注销功能会立即停用账户')
    expect(terms).toContain('当前注销会立即停用账户')
    expect(terms).not.toContain('资料可选择')
  })

  it('keeps the student-run disclaimer and copyright route visible', () => {
    expect(privacy).toContain('不是四川大学官方网站或下属机构')
    expect(terms).toContain('不是四川大学官方网站、下属机构或附属组织')
    expect(terms).toContain('href="/copyright"')
  })
})
