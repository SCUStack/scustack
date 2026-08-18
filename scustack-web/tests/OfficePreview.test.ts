import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'
import { mount } from '@vue/test-utils'

vi.stubGlobal('ref', ref)
vi.stubGlobal('computed', computed)
vi.stubGlobal('useWatermark', () => ({ watermarkStyle: computed(() => ({})) }))

describe('OfficePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uses the configured browser-reachable preview service', async () => {
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { officePreviewBase: 'https://office.example.com/' },
    }))

    const { default: OfficePreview } = await import('../components/preview/OfficePreview.vue')
    const wrapper = mount(OfficePreview, {
      props: {
        url: 'https://api.example.com/api/v1/materials/material-id/preview',
        downloadUrl: 'https://api.example.com/api/v1/materials/material-id/download',
        format: 'docx',
      },
    })

    const iframe = wrapper.get('iframe')
    expect(iframe.attributes('title')).toBe('Office 文档预览')
    expect(iframe.attributes('src')).toBe(
      'https://office.example.com/doceditor?directUrl=https%3A%2F%2Fapi.example.com%2Fapi%2Fv1%2Fmaterials%2Fmaterial-id%2Fpreview&mode=view&lang=zh',
    )
  })

  it('offers the download when no preview service is configured', async () => {
    vi.stubGlobal('useRuntimeConfig', () => ({ public: { officePreviewBase: '' } }))

    const { default: OfficePreview } = await import('../components/preview/OfficePreview.vue')
    const wrapper = mount(OfficePreview, {
      props: {
        url: 'https://api.example.com/api/v1/materials/material-id/preview',
        downloadUrl: 'https://api.example.com/api/v1/materials/material-id/download',
        format: 'docx',
      },
    })

    expect(wrapper.text()).toContain('Office 文档预览服务未配置')
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.get('a').attributes('href')).toBe(
      'https://api.example.com/api/v1/materials/material-id/download',
    )
  })
})
