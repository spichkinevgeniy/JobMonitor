import type {
  Skill,
  SpecialtyId,
  SpecialtyStepInitialValue,
} from '@/features/onboarding/ui/SpecialtyStep'
import type { SalaryStepValue } from '@/features/onboarding/ui/SalaryStep'
import type { LevelId } from '@/features/onboarding/ui/LevelStep'
import type { WorkFormatId } from '@/features/onboarding/ui/WorkFormatStep'

export interface OnboardingDraft {
  specialty: SpecialtyId | null
  skills: Skill[]
  workFormats: WorkFormatId[]
  salary: SalaryStepValue
  level: LevelId | null
}

export interface CompletedOnboardingValue {
  specialty: SpecialtyId
  skills: Skill[]
  workFormats: WorkFormatId[]
  salary: SalaryStepValue
  level: LevelId
}

export interface OnboardingPageProps {
  initialValue?: SpecialtyStepInitialValue
  onBack?: () => void
  onComplete?: (value: CompletedOnboardingValue) => void
}
