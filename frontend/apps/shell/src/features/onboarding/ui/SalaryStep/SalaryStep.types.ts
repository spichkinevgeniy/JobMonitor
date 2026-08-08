export type SalaryMode = 'any' | 'from'

export interface SalaryStepValue {
  mode: SalaryMode
  amount: number | null
}

export interface SalaryStepProps {
  initialValue?: SalaryStepValue
  maxVisitedStep?: number
  onBack?: (value: SalaryStepValue) => void
  onContinue?: (value: SalaryStepValue) => void
  onNavigateToStep?: (step: number, value: SalaryStepValue) => void
}
