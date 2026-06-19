import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  materialCategories,
  searchFilterGroups,
  searchSortOptions,
  sourceTypeOptions,
  trustStatusOptions,
} from '../data/business'

function loadBackendContracts() {
  const currentDir = dirname(fileURLToPath(import.meta.url))
  const root = resolve(currentDir, '..', '..')
  const output = execFileSync(
    'python',
    ['scustack-api/scripts/export_frontend_contracts.py'],
    { cwd: root, encoding: 'utf-8' },
  )
  return JSON.parse(output) as {
    search_sorts: Array<{ key: string; label: string }>
    search_filter_groups_meta: Array<{ key: string; label: string }>
    search_filter_static_options: Record<string, Array<{ value: string; label: string }>>
  }
}

describe('frontend/backend business contract consistency', () => {
  it('keeps search sort options aligned with backend-supported sorts', () => {
    const backend = loadBackendContracts()
    expect(searchSortOptions.map(option => ({ key: option.key, label: option.label }))).toEqual(backend.search_sorts)
  })

  it('keeps shared filter group order and labels aligned with backend contract', () => {
    const backend = loadBackendContracts()
    expect(
      searchFilterGroups
        .filter(group => group.key !== 'semester')
        .map(group => ({ key: group.key, label: group.label })),
    ).toEqual(
      backend.search_filter_groups_meta
        .filter(group => group.key !== 'semester')
        .map(group => ({ key: group.key, label: group.label })),
    )
  })

  it('keeps shared enum options aligned with backend-supported values', () => {
    const backend = loadBackendContracts()
    expect(materialCategories.map(value => ({ value, label: value }))).toEqual(backend.search_filter_static_options.category)
    expect(sourceTypeOptions.map(option => ({ value: option.value, label: option.label }))).toEqual(backend.search_filter_static_options.source_type)
    expect(trustStatusOptions.map(option => ({ value: option.value, label: option.label }))).toEqual(backend.search_filter_static_options.trust_status)
  })
})
