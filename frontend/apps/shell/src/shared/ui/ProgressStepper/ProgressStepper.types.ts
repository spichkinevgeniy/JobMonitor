export interface ProgressStepperProps {
  currentStep: number
  totalSteps: number
  maxVisitedStep?: number
  'aria-label'?: string
  onStepClick?: (step: number) => void
}
