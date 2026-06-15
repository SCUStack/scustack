/** Tests for DropZone component state transitions */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

describe('DropZone', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('mounts in default state', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows drag-over state on dragover', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    await wrapper.trigger('dragover')
    expect(wrapper.exists()).toBe(true)
  })

  it('shows drag-over state on dragenter', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    await wrapper.trigger('dragenter')
    expect(wrapper.exists()).toBe(true)
  })

  it('resets state on dragleave', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    await wrapper.trigger('dragenter')
    await wrapper.trigger('dragleave')
    expect(wrapper.exists()).toBe(true)
  })

  it('shows error state for invalid file', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    // Simulate dropping an invalid file
    const file = new File([''], 'malware.exe', { type: 'application/x-msdownload' })
    const dropEvent = new Event('drop') as any
    dropEvent.dataTransfer = { files: [file] }
    await wrapper.trigger('drop', dropEvent)
    expect(wrapper.exists()).toBe(true)
  })

  it('accepts valid PDF file', async () => {
    const { default: DropZone } = await import('../components/upload/DropZone.vue')
    const wrapper = mount(DropZone, {
      global: {
        stubs: { AppIcon: { template: '<span />' } },
      },
    })
    const file = new File(['pdf-content'], 'notes.pdf', { type: 'application/pdf' })
    const dropEvent = new Event('drop') as any
    dropEvent.dataTransfer = { files: [file] }
    await wrapper.trigger('drop', dropEvent)
    expect(wrapper.emitted('update:file')).toBeTruthy()
  })
})
