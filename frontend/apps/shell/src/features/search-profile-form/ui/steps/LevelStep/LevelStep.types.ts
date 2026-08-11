import type { SalaryStepValue } from '@/features/search-profile-form/ui/steps/SalaryStep'
import type {
  Skill,
  SpecialtyId,
} from '@/features/search-profile-form/ui/steps/SpecialtyStep'
import type { WorkFormatId } from '@/features/search-profile-form/ui/steps/WorkFormatStep'
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
  saving?: boolean
  saveError?: string | null
  summary: LevelStepSummary
  onBack?: (value: LevelStepInitialValue) => void
  onComplete?: (value: LevelStepValue) => void
  onNavigateToStep?: (step: number, value: LevelStepInitialValue) => void
}
