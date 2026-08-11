import type { LevelId } from '@/features/search-profile-form/ui/steps/LevelStep'
import type { SalaryStepValue } from '@/features/search-profile-form/ui/steps/SalaryStep'
import type {
  Skill,
  SpecialtyId,
} from '@/features/search-profile-form/ui/steps/SpecialtyStep'
import type { WorkFormatId } from '@/features/search-profile-form/ui/steps/WorkFormatStep'

export interface SearchProfileFormValues {
  specialty: SpecialtyId | null
  skills: Skill[]
  workFormats: WorkFormatId[]
  salary: SalaryStepValue
  level: LevelId | null
}

export interface CompletedSearchProfileValue extends SearchProfileFormValues {
  specialty: SpecialtyId
  level: LevelId
}
