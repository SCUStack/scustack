import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const toastMocks = vi.hoisted(() => ({
  success: vi.fn(),
}))

const runtimeConfigMock = vi.hoisted(() => ({
  public: { apiBase: 'http://api.test' },
}))

const navigateToMock = vi.hoisted(() => vi.fn())

vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('useRuntimeConfig', () => runtimeConfigMock)
vi.stubGlobal('useToast', () => toastMocks)
vi.stubGlobal('navigateTo', navigateToMock)

const dropZoneApi = {
  setUploading: vi.fn(),
}

async function mountPage() {
  const { default: UploadPage } = await import('../pages/upload.vue')
  return mount(UploadPage, {
    global: {
      stubs: {
        AppIcon: { template: '<span />' },
        CollegeCourseSelect: {
          template: '<div />',
          emits: ['update:college-id', 'update:course-id'],
        },
        DropZone: {
          template: '<div />',
          emits: ['update:file', 'update:files'],
          methods: dropZoneApi,
        },
      },
    },
  })
}

function makeFile(name = 'notes.pdf', type = 'application/pdf', size = 4) {
  const file = new File(['test'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  Object.defineProperty(file, 'arrayBuffer', {
    value: vi.fn().mockResolvedValue(new Uint8Array([1, 2, 3, 4]).buffer),
  })
  return file
}

describe('upload page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })
    vi.stubGlobal('crypto', {
      subtle: {
        digest: vi.fn().mockResolvedValue(new Uint8Array([1, 2, 3]).buffer),
      },
    })
  })

  it('stops submission when duplicate file is reported', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ code: 0, data: { is_duplicate: true, existing_title: '旧资料' } })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = await mountPage()
    await nextTick()

    await wrapper.find('input[placeholder="输入资料的准确标题"]').setValue('新资料')
    await wrapper.find('select').setValue('2025-2026-1')
    ;(wrapper.vm as any).form.courseId = 'course-id'
    ;(wrapper.vm as any).form.category = '课堂笔记'
    ;(wrapper.vm as any).selectedFile = makeFile()

    await (wrapper.vm as any).submitSingle()
    await nextTick()

    expect(wrapper.text()).toContain('该文件已存在：旧资料')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(toastMocks.success).not.toHaveBeenCalled()
  })

  it('shows pending-review success feedback after hosted upload succeeds', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ code: 0, data: { is_duplicate: false } })
      .mockResolvedValueOnce({ code: 0, data: { upload_url: 'http://upload.test', storage_key: 'materials/test.pdf' }, message: 'ok' })
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ code: 0, data: { id: 'material-id' }, message: 'material submitted for review' })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = await mountPage()
    await nextTick()

    await wrapper.find('input[placeholder="输入资料的准确标题"]').setValue('新资料')
    await wrapper.find('select').setValue('2025-2026-1')
    ;(wrapper.vm as any).form.courseId = 'course-id'
    ;(wrapper.vm as any).form.category = '课堂笔记'
    ;(wrapper.vm as any).selectedFile = makeFile()

    await (wrapper.vm as any).submitSingle()
    await nextTick()

    expect(toastMocks.success).toHaveBeenCalledWith('资料已提交审核')
    expect(navigateToMock).toHaveBeenCalledWith('/user/contributions')
  })
})
