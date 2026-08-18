export type ApiOnboardingStep =
  | 'SPECIALTY'
  | 'WORK_FORMAT'
  | 'SALARY'
  | 'LEVEL'

export type ApiSpecialty =
  | 'Backend'
  | 'Frontend'
  | 'Data Science / ML'
  | 'Mobile'
  | 'GameDev'
  | 'QA'
  | 'Infrastructure & DevOps'
  | 'Analytics'
  | 'UI/UX & Product Design'

export type ApiSkill =
  | 'Python'
  | 'Java/Scala'
  | 'C#'
  | 'C++'
  | 'Go'
  | 'Rust'
  | 'C'
  | 'Ruby'
  | 'PHP'
  | 'Node.js'
  | 'TypeScript'
  | 'JavaScript'
  | 'Kotlin'
  | 'React'
  | 'Vue'
  | 'Angular'
  | 'Machine Learning'
  | 'NLP'
  | 'Computer Vision'
  | 'iOS'
  | 'Android'
  | 'Flutter'
  | 'React Native'
  | 'Unity'
  | 'Unreal Engine'
  | 'Graphics'
  | 'Manual QA'
  | 'QA Automation'
  | 'DevOps'
  | 'Docker'
  | 'SRE'
  | 'System Administration'
  | 'SQL'
  | 'Data Analysis'
  | 'Data Engineering'

export type ApiWorkFormat = 'ANY' | 'REMOTE' | 'HYBRID' | 'ONSITE'
export type ApiSalaryMode = 'ANY' | 'FROM'
export type ApiOnboardingLevel =
  | 'INTERN'
  | 'JUNIOR'
  | 'JUNIOR_PLUS'
  | 'MIDDLE'
  | 'SENIOR'

export interface ApiSalaryDraft {
  mode: ApiSalaryMode
  amount_rub: number | null
}

export interface ApiOnboardingDraft {
  specializations: ApiSpecialty[]
  /** Temporary backend compatibility field for older clients. */
  specialty: ApiSpecialty | null
  skills: ApiSkill[]
  work_formats: ApiWorkFormat[] | null
  salary: ApiSalaryDraft | null
  level: ApiOnboardingLevel | null
}

export interface OnboardingStateResponse {
  completed: boolean
  completed_at: string | null
  current_step: ApiOnboardingStep
  max_visited_step: ApiOnboardingStep
  draft: ApiOnboardingDraft
}

export interface ResumeImportJobCreated {
  job_id: string
  status: 'queued'
}

export type ResumeImportJobStatus =
  | {
      job_id: string
      status: 'queued' | 'processing'
      error: null
    }
  | {
      job_id: string
      status: 'completed'
      error: null
    }
  | {
      job_id: string
      status: 'failed'
      error: string | null
    }

interface DraftRequest<TStep extends ApiOnboardingStep, TData> {
  step: TStep
  navigate_to: ApiOnboardingStep
  data: TData
}

export type SpecialtyDraftRequest = DraftRequest<
  'SPECIALTY',
  { specializations: ApiSpecialty[]; skills: ApiSkill[] }
>
export type WorkFormatDraftRequest = DraftRequest<
  'WORK_FORMAT',
  { work_formats: ApiWorkFormat[] }
>
export type SalaryDraftRequest = DraftRequest<
  'SALARY',
  { mode: ApiSalaryMode; amount_rub: number | null }
>
export type LevelDraftRequest = DraftRequest<
  'LEVEL',
  { level: ApiOnboardingLevel }
>

export interface BackwardNavigationRequest {
  step: ApiOnboardingStep
  navigate_to: ApiOnboardingStep
  data: null
}

export type OnboardingDraftRequest =
  | SpecialtyDraftRequest
  | WorkFormatDraftRequest
  | SalaryDraftRequest
  | LevelDraftRequest
  | BackwardNavigationRequest
