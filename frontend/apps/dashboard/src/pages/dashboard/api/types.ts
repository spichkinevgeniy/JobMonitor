export type ApiWorkFormat = 'REMOTE' | 'HYBRID' | 'ONSITE'
export type ApiSalaryMode = 'ANY' | 'FROM'
export type ApiGrade = 'INTERN' | 'JUNIOR' | 'MIDDLE' | 'SENIOR' | 'LEAD'
export type ApiLevelMode = 'IGNORE' | 'UP_TO' | 'EXACT' | 'AT_LEAST'

export interface SearchProfileResponse {
  specializations: string[]
  skills: string[]
  work_formats: ApiWorkFormat[]
  salary: {
    mode: ApiSalaryMode
    amount_rub: number | null
  }
  level: {
    grade: ApiGrade | null
    mode: ApiLevelMode
  }
  search_active: boolean
}
