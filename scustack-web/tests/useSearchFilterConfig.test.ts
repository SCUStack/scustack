import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

const stateMap = new Map<string, ReturnType<typeof ref>>()

vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('useState', <T>(key: string, init: () => T) => {
  if (!stateMap.has(key)) stateMap.set(key, ref(init()))
  return stateMap.get(key)
})

describe('useSearchFilterConfig', () => {
  beforeEach(() => {
    stateMap.clear()
  })

  it('loads backend-provided filter config', async () => {
    vi.stubGlobal('$fetch', vi.fn().mockResolvedValue({
      code: 0,
      data: {
        sorts: [{ key: 'newest', label: '最新' }],
        filters: [
          {
            key: 'category',
            label: '资料分类',
            options: [{ value: '课堂笔记', label: '课堂笔记' }],
          },
        ],
      },
    }))

    const { useSearchFilterConfig } = await import('../composables/useSearchFilterConfig')
    const config = useSearchFilterConfig()
    await config.load()

    expect(config.sortOptions.value).toEqual([{ key: 'newest', label: '最新' }])
    expect(config.filterGroups.value).toEqual([
      {
        key: 'category',
        label: '资料分类',
        options: [{ value: '课堂笔记', label: '课堂笔记' }],
      },
    ])
    expect(config.loaded.value).toBe(true)
  })

  it('keeps fallback config when backend config request fails', async () => {
    vi.stubGlobal('$fetch', vi.fn().mockRejectedValue(new Error('network error')))

    const { useSearchFilterConfig } = await import('../composables/useSearchFilterConfig')
    const config = useSearchFilterConfig()
    await config.load()

    expect(config.filterGroups.value.length).toBeGreaterThan(0)
    expect(config.sortOptions.value.some(option => option.key === 'relevance')).toBe(true)
    expect(config.loaded.value).toBe(false)
  })
})
