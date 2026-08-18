import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { computed, onMounted, ref } from 'vue'

vi.stubGlobal('ref', ref)
vi.stubGlobal('computed', computed)
vi.stubGlobal('onMounted', onMounted)

describe('FilePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('includes the login cookie when loading text previews', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: vi.fn().mockResolvedValue('preview body'),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { default: FilePreview } = await import('../components/preview/FilePreview.vue')
    const wrapper = mount(FilePreview, {
      props: {
        fileUrl: 'http://api.test/api/v1/materials/material-id/preview',
        downloadUrl: 'http://api.test/api/v1/materials/material-id/download',
        format: 'txt',
        sourceType: 'hosted',
      },
      global: {
        stubs: {
          PdfPreview: { template: '<div />' },
          OfficePreview: { template: '<div />' },
          CodePreview: { template: '<div />' },
          ImagePreview: { template: '<div />' },
          TextPreview: { props: ['content'], template: '<pre>{{ content }}</pre>' },
          AppIcon: { template: '<span />' },
        },
      },
    })
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/api/v1/materials/material-id/preview',
      { credentials: 'include' },
    )
    expect(wrapper.text()).toContain('preview body')
  })
})
