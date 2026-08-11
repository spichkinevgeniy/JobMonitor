export {
  onboardingApi,
  useCompleteOnboardingMutation,
  useGetOnboardingQuery,
  useSaveOnboardingDraftMutation,
} from './onboardingApi'
export {
  backwardNavigationRequest,
  levelDraftRequest,
  onboardingStateToDraft,
  onboardingStepFromNumber,
  onboardingStepToNumber,
  salaryDraftRequest,
  specialtyDraftRequest,
  workFormatDraftRequest,
  workFormatsFromApi,
  workFormatsToApi,
} from './mappers'
export type {
  ApiOnboardingStep,
  ApiWorkFormat,
  BackwardNavigationRequest,
  OnboardingDraftRequest,
  OnboardingStateResponse,
} from './types'
