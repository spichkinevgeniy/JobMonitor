import type { SalaryStepValue } from '@/features/onboarding/ui/SalaryStep'
import type {
  Skill,
  SpecialtyId,
} from '@/features/onboarding/ui/SpecialtyStep'
import type { WorkFormatId } from '@/features/onboarding/ui/WorkFormatStep'
import type { levels } from './LevelStep.config'

export type LevelId = (typeof levels)[number]['id']

export interface LevelStepValue {
  level: LevelId
}

export interface LevelStepInitialValue {
  level: LevelId | null
}

export interface LevelStepSummary {
  specialty: SpecialtyId
  skills: Skill[]
  workFormats: WorkFormatId[]
  salary: SalaryStepValue
}

export interface LevelStepProps {
  initialValue?: LevelStepInitialValue
  maxVisitedStep?: number
  summary: LevelStepSummary
  onBack?: (value: LevelStepInitialValue) => void
  onComplete?: (value: LevelStepValue) => void
  onNavigateToStep?: (step: number, value: LevelStepInitialValue) => void
}
