import { describe, expect, it } from 'vitest'

import {
  businessLabelMaps,
  materialCategories,
  searchFilterGroups,
  sourceTypeOptions,
  trustStatusConfig,
} from '../data/business'

describe('business option source of truth', () => {
  it('exposes every material category through the shared search filter config', () => {
    const categoryGroup = searchFilterGroups.find(group => group.key === 'category')
    expect(categoryGroup?.options.map(option => option.value)).toEqual([...materialCategories])
  })

  it('derives trust and source-type labels from the shared config', () => {
    expect(Object.keys(businessLabelMaps.trust_status)).toEqual(Object.keys(trustStatusConfig))
    expect(Object.keys(businessLabelMaps.source_type)).toEqual(sourceTypeOptions.map(option => option.value))
  })
})
