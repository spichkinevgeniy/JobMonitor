import type { SearchProfile } from '../model/types'
import type {
  ApiGrade,
  ApiLevelMode,
  ApiWorkFormat,
  SearchProfileResponse,
} from './types'

const specializationLabels: Record<string, string> = {
  Analytics: 'Аналитика',
  Design: 'Дизайн',
  'Infrastructure & DevOps': 'DevOps',
}

const workFormatLabels = {
  REMOTE: 'Удалённо',
  HYBRID: 'Гибрид',
  ONSITE: 'В офисе',
} as const satisfies Record<ApiWorkFormat, string>

const gradeLabels = {
  INTERN: 'Стажёр',
  JUNIOR: 'Junior',
  MIDDLE: 'Middle',
  SENIOR: 'Senior',
  LEAD: 'Lead',
} as const satisfies Record<ApiGrade, string>

const formatLevel = (grade: ApiGrade | null, mode: ApiLevelMode): string => {
  if (mode === 'IGNORE' || grade === null) {
    return 'Любой уровень'
  }

  const label = gradeLabels[grade]
  if (mode === 'AT_LEAST') {
    return `${label}+`
  }
  if (mode === 'UP_TO') {
    return `до ${label}`
  }
  return label
}

const formatSalary = (response: SearchProfileResponse['salary']): string => {
  if (response.mode !== 'FROM' || response.amount_rub === null) {
    return 'Любая зарплата'
  }

  const amount = new Intl.NumberFormat('ru-RU')
    .format(response.amount_rub)
    .replace(/[\u00a0\u202f]/g, ' ')
  return `от ${amount} ₽`
}

export const searchProfileFromApi = (
  response: SearchProfileResponse,
): SearchProfile => ({
  specialization: response.specializations
    .map((value) => specializationLabels[value] ?? value)
    .join(', '),
  skills: response.skills,
  workFormat:
    response.work_formats.length === 0
      ? 'Любой формат'
      : response.work_formats.map((value) => workFormatLabels[value]).join(', '),
  salary: formatSalary(response.salary),
  level: formatLevel(response.level.grade, response.level.mode),
  searchActive: response.search_active,
})
