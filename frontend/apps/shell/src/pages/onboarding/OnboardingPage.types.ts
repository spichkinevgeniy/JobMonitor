import type { CompletedSearchProfileValue } from '@/features/search-profile-form'
import type { SpecialtyStepInitialValue } from '@/features/search-profile-form/ui/steps/SpecialtyStep'

export type { CompletedSearchProfileValue }

export interface OnboardingPageProps {
  initialValue?: SpecialtyStepInitialValue
  onBack?: () => void
  onComplete?: (value: CompletedSearchProfileValue) => void
}
