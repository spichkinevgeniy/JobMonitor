import { describe, expect, it } from 'vitest'

import { searchProfileFromApi } from './mappers'
import type { SearchProfileResponse } from './types'

const response = {
  specializations: ['Frontend', 'Analytics'],
  skills: ['React', 'TypeScript'],
  work_formats: ['REMOTE', 'HYBRID'],
  salary: { mode: 'FROM', amount_rub: 150000 },
  level: { grade: 'JUNIOR', mode: 'AT_LEAST' },
  search_active: true,
} satisfies SearchProfileResponse

describe('searchProfileFromApi', () => {
  it('maps backend enums and filter modes into the approved UI model', () => {
    expect(searchProfileFromApi(response)).toEqual({
      specialization: 'Frontend, Аналитика',
      skills: ['React', 'TypeScript'],
      workFormat: 'Удалённо, Гибрид',
      salary: 'от 150 000 ₽',
      level: 'Junior+',
      searchActive: true,
    })
  })

  it('maps unconstrained filters without inventing profile values', () => {
    expect(
      searchProfileFromApi({
        ...response,
        work_formats: [],
        salary: { mode: 'ANY', amount_rub: null },
        level: { grade: null, mode: 'IGNORE' },
        search_active: false,
      }),
    ).toMatchObject({
      workFormat: 'Любой формат',
      salary: 'Любая зарплата',
      level: 'Любой уровень',
      searchActive: false,
    })
  })

  it('maps exact and upper-bound level modes explicitly', () => {
    expect(
      searchProfileFromApi({
        ...response,
        level: { grade: 'MIDDLE', mode: 'EXACT' },
      }).level,
    ).toBe('Middle')
    expect(
      searchProfileFromApi({
        ...response,
        level: { grade: 'SENIOR', mode: 'UP_TO' },
      }).level,
    ).toBe('до Senior')
  })
})
