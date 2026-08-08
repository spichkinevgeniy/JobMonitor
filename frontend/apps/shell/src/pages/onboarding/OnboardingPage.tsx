import { useEffect, useState } from 'react'

import {
  isSkill,
  isSpecialtyId,
  SpecialtyStep,
} from '@/features/onboarding/ui/SpecialtyStep'
import type {
  SpecialtyStepInitialValue,
  SpecialtyStepValue,
} from '@/features/onboarding/ui/SpecialtyStep'
import { LevelStep } from '@/features/onboarding/ui/LevelStep'
import type {
  LevelStepInitialValue,
  LevelStepValue,
} from '@/features/onboarding/ui/LevelStep'
import { SalaryStep } from '@/features/onboarding/ui/SalaryStep'
import type { SalaryStepValue } from '@/features/onboarding/ui/SalaryStep'
import { WorkFormatStep } from '@/features/onboarding/ui/WorkFormatStep'
import type {
  WorkFormatStepValue,
} from '@/features/onboarding/ui/WorkFormatStep'
import { telegramGet } from '@/shared/api'
import { isTelegramEnvironment } from '@/shared/lib/telegram'
import type {
  OnboardingDraft,
  OnboardingPageProps,
} from './OnboardingPage.types'

interface SpecialtyReadResponse {
  specializations: string[]
  skills: string[]
}

type OnboardingStep = 1 | 2 | 3 | 4

const isSpecialtyReadResponse = (
  payload: unknown,
): payload is SpecialtyReadResponse => {
  if (typeof payload !== 'object' || payload === null) {
    return false
  }

  const response = payload as Record<string, unknown>

  return (
    Array.isArray(response.specializations) &&
    response.specializations.every((item) => typeof item === 'string') &&
    Array.isArray(response.skills) &&
    response.skills.every((item) => typeof item === 'string')
  )
}

const createInitialDraft = (
  initialValue: SpecialtyStepInitialValue | undefined,
): OnboardingDraft => ({
  specialty: isSpecialtyId(initialValue?.specialty)
    ? initialValue.specialty
    : null,
  skills: (initialValue?.skills ?? []).filter(isSkill),
  workFormats: [],
  salary: {
    mode: 'any',
    amount: null,
  },
  level: null,
})

export const OnboardingPage = ({
  initialValue,
  onBack,
  onComplete,
}: OnboardingPageProps) => {
  const shouldLoadInitialValue =
    initialValue === undefined && isTelegramEnvironment()
  const [currentStep, setCurrentStep] = useState<OnboardingStep>(1)
  const [maxVisitedStep, setMaxVisitedStep] = useState<OnboardingStep>(1)
  const [draft, setDraft] = useState<OnboardingDraft>(() =>
    createInitialDraft(initialValue),
  )
  const [isInitialValueReady, setIsInitialValueReady] = useState(
    !shouldLoadInitialValue,
  )

  useEffect(() => {
    if (!shouldLoadInitialValue) {
      return
    }

    const controller = new AbortController()

    const loadSpecialty = async () => {
      try {
        const payload = await telegramGet<unknown>('/miniapp/api/specialty', {
          signal: controller.signal,
        })

        if (isSpecialtyReadResponse(payload)) {
          setDraft((currentDraft) => ({
            ...currentDraft,
            specialty: payload.specializations.find(isSpecialtyId) ?? null,
            skills: payload.skills.filter(isSkill),
          }))
        }
      } catch (requestError) {
        if (!controller.signal.aborted) {
          console.error('Не удалось загрузить specialty.', requestError)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsInitialValueReady(true)
        }
      }
    }

    void loadSpecialty()

    return () => controller.abort()
  }, [shouldLoadInitialValue])

  const handleFirstStepBack = () => {
    if (onBack) {
      onBack()
      return
    }

    if (window.history.length > 1) {
      window.history.back()
    }
  }

  const advanceToStep = (step: OnboardingStep) => {
    setMaxVisitedStep((currentMax) =>
      currentMax >= step ? currentMax : step,
    )
    setCurrentStep(step)
  }

  const navigateToVisitedStep = (targetStep: number) => {
    if (
      !Number.isInteger(targetStep) ||
      targetStep < 1 ||
      targetStep > maxVisitedStep ||
      targetStep === currentStep
    ) {
      return
    }

    setCurrentStep(targetStep as OnboardingStep)
  }

  const handleSpecialtyContinue = (value: SpecialtyStepValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      specialty: value.specialty,
      skills: value.skills,
    }))
    advanceToStep(2)
  }

  const handleSpecialtyNavigation = (
    targetStep: number,
    value: SpecialtyStepValue,
  ) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      specialty: value.specialty,
      skills: value.skills,
    }))
    navigateToVisitedStep(targetStep)
  }

  const handleWorkFormatContinue = (value: WorkFormatStepValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      workFormats: value.workFormats,
    }))
    advanceToStep(3)
  }

  const handleWorkFormatBack = (value: WorkFormatStepValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      workFormats: value.workFormats,
    }))
    setCurrentStep(1)
  }

  const handleWorkFormatNavigation = (
    targetStep: number,
    value: WorkFormatStepValue,
  ) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      workFormats: value.workFormats,
    }))
    navigateToVisitedStep(targetStep)
  }

  const handleSalaryContinue = (value: SalaryStepValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      salary: value,
    }))
    advanceToStep(4)
  }

  const handleSalaryBack = (value: SalaryStepValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      salary: value,
    }))
    setCurrentStep(2)
  }

  const handleSalaryNavigation = (
    targetStep: number,
    value: SalaryStepValue,
  ) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      salary: value,
    }))
    navigateToVisitedStep(targetStep)
  }

  const handleLevelBack = (value: LevelStepInitialValue) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      level: value.level,
    }))
    setCurrentStep(3)
  }

  const handleLevelNavigation = (
    targetStep: number,
    value: LevelStepInitialValue,
  ) => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      level: value.level,
    }))
    navigateToVisitedStep(targetStep)
  }

  const handleLevelComplete = (value: LevelStepValue) => {
    const completedDraft: OnboardingDraft = {
      ...draft,
      level: value.level,
    }

    setDraft(completedDraft)

    const hasValidSalary =
      completedDraft.salary.mode === 'any' ||
      (completedDraft.salary.amount !== null &&
        completedDraft.salary.amount > 0)

    if (
      completedDraft.specialty === null ||
      completedDraft.workFormats.length === 0 ||
      !hasValidSalary
    ) {
      return
    }

    onComplete?.({
      specialty: completedDraft.specialty,
      skills: completedDraft.skills,
      workFormats: completedDraft.workFormats,
      salary: completedDraft.salary,
      level: value.level,
    })
  }

  if (!isInitialValueReady) {
    return null
  }

  if (currentStep === 4) {
    if (draft.specialty === null) {
      return null
    }

    return (
      <LevelStep
        initialValue={{ level: draft.level }}
        maxVisitedStep={maxVisitedStep}
        summary={{
          specialty: draft.specialty,
          skills: draft.skills,
          workFormats: draft.workFormats,
          salary: draft.salary,
        }}
        onBack={handleLevelBack}
        onComplete={handleLevelComplete}
        onNavigateToStep={handleLevelNavigation}
      />
    )
  }

  if (currentStep === 3) {
    return (
      <SalaryStep
        initialValue={draft.salary}
        maxVisitedStep={maxVisitedStep}
        onBack={handleSalaryBack}
        onContinue={handleSalaryContinue}
        onNavigateToStep={handleSalaryNavigation}
      />
    )
  }

  if (currentStep === 2) {
    return (
      <WorkFormatStep
        initialValue={{ workFormats: draft.workFormats }}
        maxVisitedStep={maxVisitedStep}
        onBack={handleWorkFormatBack}
        onContinue={handleWorkFormatContinue}
        onNavigateToStep={handleWorkFormatNavigation}
      />
    )
  }

  return (
    <SpecialtyStep
      initialValue={{
        specialty: draft.specialty,
        skills: draft.skills,
      }}
      maxVisitedStep={maxVisitedStep}
      onBack={handleFirstStepBack}
      onContinue={handleSpecialtyContinue}
      onNavigateToStep={handleSpecialtyNavigation}
    />
  )
}
