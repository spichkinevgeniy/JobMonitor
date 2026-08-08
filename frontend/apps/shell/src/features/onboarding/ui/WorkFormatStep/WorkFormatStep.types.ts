export type WorkFormatId = 'any' | 'remote' | 'hybrid' | 'office'

export interface WorkFormatStepValue {
  workFormats: WorkFormatId[]
}

export interface WorkFormatStepProps {
  initialValue?: WorkFormatStepValue
  maxVisitedStep?: number
  onBack?: (value: WorkFormatStepValue) => void
  onContinue?: (value: WorkFormatStepValue) => void
  onNavigateToStep?: (step: number, value: WorkFormatStepValue) => void
}
