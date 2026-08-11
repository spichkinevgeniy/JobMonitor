import type { SearchProfileFormValues } from '@/features/search-profile-form/model'
import { levels } from '@/features/search-profile-form/ui/steps/LevelStep/LevelStep.config'
import type { LevelId } from '@/features/search-profile-form/ui/steps/LevelStep'
import type { SalaryStepValue } from '@/features/search-profile-form/ui/steps/SalaryStep'
import {
  isSkill,
  isSpecialtyId,
  type SpecialtyStepValue,
} from '@/features/search-profile-form/ui/steps/SpecialtyStep'
import type {
  WorkFormatId,
  WorkFormatStepValue,
} from '@/features/search-profile-form/ui/steps/WorkFormatStep'
import type {
  ApiOnboardingLevel,
  ApiOnboardingStep,
  ApiWorkFormat,
  BackwardNavigationRequest,
  LevelDraftRequest,
  OnboardingStateResponse,
  SalaryDraftRequest,
  SpecialtyDraftRequest,
  WorkFormatDraftRequest,
} from './types'

const frontendToApiWorkFormat = {
  any: 'ANY',
  remote: 'REMOTE',
  hybrid: 'HYBRID',
  office: 'ONSITE',
} as const satisfies Record<WorkFormatId, ApiWorkFormat>

const apiToFrontendWorkFormat = {
  ANY: 'any',
  REMOTE: 'remote',
  HYBRID: 'hybrid',
  ONSITE: 'office',
} as const satisfies Record<ApiWorkFormat, WorkFormatId>

export const onboardingStepToNumber = (
  step: ApiOnboardingStep,
): 1 | 2 | 3 | 4 =>
  ({ SPECIALTY: 1, WORK_FORMAT: 2, SALARY: 3, LEVEL: 4 })[step] as
    | 1
    | 2
    | 3
    | 4

export const onboardingStepFromNumber = (
  step: 1 | 2 | 3 | 4,
): ApiOnboardingStep =>
  ({ 1: 'SPECIALTY', 2: 'WORK_FORMAT', 3: 'SALARY', 4: 'LEVEL' })[step] as ApiOnboardingStep

export const workFormatsToApi = (
  workFormats: WorkFormatId[],
): ApiWorkFormat[] => workFormats.map((value) => frontendToApiWorkFormat[value])

export const workFormatsFromApi = (
  workFormats: ApiWorkFormat[] | null,
): WorkFormatId[] =>
  workFormats?.map((value) => apiToFrontendWorkFormat[value]) ?? []

export const onboardingStateToDraft = (
  response: OnboardingStateResponse,
): SearchProfileFormValues => ({
  specializations: response.draft.specializations.filter(isSpecialtyId),
  skills: response.draft.skills.filter(isSkill),
  workFormats: workFormatsFromApi(response.draft.work_formats),
  salary: response.draft.salary
    ? {
        mode: response.draft.salary.mode === 'FROM' ? 'from' : 'any',
        amount: response.draft.salary.amount_rub,
      }
    : { mode: 'any', amount: null },
  level: isLevelId(response.draft.level) ? response.draft.level : null,
})

export const specialtyDraftRequest = (
  value: SpecialtyStepValue,
  navigateTo: ApiOnboardingStep,
): SpecialtyDraftRequest => ({
  step: 'SPECIALTY',
  navigate_to: navigateTo,
  data: { specializations: value.specializations, skills: value.skills },
})

export const workFormatDraftRequest = (
  value: WorkFormatStepValue,
  navigateTo: ApiOnboardingStep,
): WorkFormatDraftRequest => ({
  step: 'WORK_FORMAT',
  navigate_to: navigateTo,
  data: { work_formats: workFormatsToApi(value.workFormats) },
})

export const salaryDraftRequest = (
  value: SalaryStepValue,
  navigateTo: ApiOnboardingStep,
): SalaryDraftRequest => ({
  step: 'SALARY',
  navigate_to: navigateTo,
  data: {
    mode: value.mode === 'from' ? 'FROM' : 'ANY',
    amount_rub: value.mode === 'from' ? value.amount : null,
  },
})

export const levelDraftRequest = (
  level: LevelId,
  navigateTo: ApiOnboardingStep,
): LevelDraftRequest => ({
  step: 'LEVEL',
  navigate_to: navigateTo,
  data: { level },
})

export const backwardNavigationRequest = (
  currentStep: ApiOnboardingStep,
  navigateTo: ApiOnboardingStep,
): BackwardNavigationRequest => ({
  step: currentStep,
  navigate_to: navigateTo,
  data: null,
})

const isLevelId = (
  level: ApiOnboardingLevel | null,
): level is LevelId => levels.some((item) => item.id === level)
