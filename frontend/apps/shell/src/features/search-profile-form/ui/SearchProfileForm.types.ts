import type { CompletedSearchProfileValue } from '../model'
import type { SpecialtyStepInitialValue } from './steps/SpecialtyStep'

export interface SearchProfileFormProps {
  initialValues?: SpecialtyStepInitialValue
  showInitiallyCompleted?: boolean
  completionDescription?: string
  onBack?: () => void
  onComplete?: (value: CompletedSearchProfileValue) => void
  onResumeSelected?: (file: File) => void
}
