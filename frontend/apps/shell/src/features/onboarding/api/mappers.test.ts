import { describe, expect, it } from 'vitest'

import { workFormatsFromApi, workFormatsToApi } from './mappers'

describe('work format transport mapping', () => {
  it('maps frontend values to backend values explicitly', () => {
    expect(workFormatsToApi(['any'])).toEqual(['ANY'])
    expect(workFormatsToApi(['remote', 'hybrid', 'office'])).toEqual([
      'REMOTE',
      'HYBRID',
      'ONSITE',
    ])
  })

  it('maps backend values without leaking transport enums into UI state', () => {
    expect(workFormatsFromApi(['ANY'])).toEqual(['any'])
    expect(workFormatsFromApi(['REMOTE', 'HYBRID', 'ONSITE'])).toEqual([
      'remote',
      'hybrid',
      'office',
    ])
    expect(workFormatsFromApi(null)).toEqual([])
  })
})
