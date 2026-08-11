export type SpecialtyId =
  | 'Frontend'
  | 'Backend'
  | 'QA'
  | 'Analytics'
  | 'Infrastructure & DevOps'
  | 'UI/UX & Product Design'

export type Skill =
  | 'React'
  | 'TypeScript'
  | 'JavaScript'
  | 'Node.js'
  | 'Python'
  | 'SQL'
  | 'Docker'

export interface SpecialtyStepValue {
  specializations: SpecialtyId[]
  skills: Skill[]
}

export interface SpecialtyStepInitialValue {
  specializations: string[]
  skills: string[]
}

export interface SpecialtyStepProps {
  initialValue?: SpecialtyStepInitialValue
  maxVisitedStep?: number
  saving?: boolean
  saveError?: string | null
  onBack?: () => void
  onContinue?: (value: SpecialtyStepValue) => void
  onNavigateToStep?: (step: number, value: SpecialtyStepValue) => void
}
