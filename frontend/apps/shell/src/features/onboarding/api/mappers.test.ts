import { describe, expect, it } from 'vitest'

import {
  specialtyDraftRequest,
  workFormatsFromApi,
  workFormatsToApi,
} from './mappers'

describe('specialization transport mapping', () => {
  it('keeps every selected specialization in the draft request', () => {
    expect(
      specialtyDraftRequest(
        {
          specializations: ['Frontend', 'Backend'],
          skills: ['React'],
        },
        'WORK_FORMAT',
      ),
    ).toEqual({
      step: 'SPECIALTY',
      navigate_to: 'WORK_FORMAT',
      data: {
        specializations: ['Frontend', 'Backend'],
        skills: ['React'],
      },
    })
  })
})

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
