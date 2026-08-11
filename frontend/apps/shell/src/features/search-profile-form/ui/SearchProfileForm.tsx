import { Box, CircularProgress, Typography } from '@mui/material'
import { useCallback, useEffect, useRef, useState } from 'react'

import {
  backwardNavigationRequest,
  levelDraftRequest,
  onboardingStateToDraft,
  onboardingStepFromNumber,
  onboardingStepToNumber,
  salaryDraftRequest,
  specialtyDraftRequest,
  useCompleteOnboardingMutation,
  useGetOnboardingQuery,
  useSaveOnboardingDraftMutation,
  workFormatDraftRequest,
  type OnboardingDraftRequest,
  type OnboardingStateResponse,
} from '@/features/onboarding/api'
import type { SearchProfileFormValues } from '@/features/search-profile-form/model'
import { LevelStep } from '@/features/search-profile-form/ui/steps/LevelStep'
import type {
  LevelStepInitialValue,
  LevelStepValue,
} from '@/features/search-profile-form/ui/steps/LevelStep'
import { SalaryStep } from '@/features/search-profile-form/ui/steps/SalaryStep'
import type { SalaryStepValue } from '@/features/search-profile-form/ui/steps/SalaryStep'
import {
  isSkill,
  isSpecialtyId,
  SpecialtyStep,
} from '@/features/search-profile-form/ui/steps/SpecialtyStep'
import type {
  SpecialtyStepInitialValue,
  SpecialtyStepValue,
} from '@/features/search-profile-form/ui/steps/SpecialtyStep'
import { WorkFormatStep } from '@/features/search-profile-form/ui/steps/WorkFormatStep'
import type { WorkFormatStepValue } from '@/features/search-profile-form/ui/steps/WorkFormatStep'
import { Button } from '@/shared/ui/Button'
import type { SearchProfileFormProps } from './SearchProfileForm.types'

type SearchProfileFormStep = 1 | 2 | 3 | 4

const createInitialDraft = (
  initialValues: SpecialtyStepInitialValue | undefined,
): SearchProfileFormValues => ({
  specializations: (initialValues?.specializations ?? []).filter(isSpecialtyId),
  skills: (initialValues?.skills ?? []).filter(isSkill),
  workFormats: [],
  salary: { mode: 'any', amount: null },
  level: null,
})

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (typeof error !== 'object' || error === null) {
    return fallback
  }

  if ('data' in error && typeof error.data === 'object' && error.data !== null) {
    const data = error.data as Record<string, unknown>
    if (typeof data.detail === 'string') {
      return data.detail
    }
  }

  if ('error' in error && typeof error.error === 'string') {
    return error.error
  }

  return fallback
}

interface StatusScreenProps {
  title: string
  description: string
  loading?: boolean
  actionLabel?: string
  onAction?: () => void
}

const StatusScreen = ({
  title,
  description,
  loading = false,
  actionLabel,
  onAction,
}: StatusScreenProps) => (
  <Box
    component="main"
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      maxWidth: 420,
      minHeight: '100dvh',
      mx: 'auto',
      px: 2,
      py: 'calc(32px + env(safe-area-inset-top))',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      bgcolor: 'background.default',
    }}
  >
    {loading && <CircularProgress size={28} sx={{ mb: 2 }} />}
    <Typography component="h1" sx={{ fontSize: 24, fontWeight: 700 }}>
      {title}
    </Typography>
    <Typography sx={{ mt: 1, color: 'text.secondary', fontSize: 15 }}>
      {description}
    </Typography>
    {actionLabel && onAction && (
      <Button sx={{ mt: 3 }} onClick={onAction}>
        {actionLabel}
      </Button>
    )}
  </Box>
)

export const SearchProfileForm = ({
  initialValues,
  showInitiallyCompleted = true,
  completionDescription = 'Ваш профиль поиска уже настроен.',
  onBack,
  onComplete,
}: SearchProfileFormProps) => {
  const standalone = initialValues !== undefined
  const [currentStep, setCurrentStep] = useState<SearchProfileFormStep>(1)
  const [maxVisitedStep, setMaxVisitedStep] = useState<SearchProfileFormStep>(1)
  const [draft, setDraft] = useState<SearchProfileFormValues>(() =>
    createInitialDraft(initialValues),
  )
  const [hydrated, setHydrated] = useState(standalone)
  const [showSuccess, setShowSuccess] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const requestPendingRef = useRef(false)

  const onboardingQuery = useGetOnboardingQuery(undefined, { skip: standalone })
  const [saveDraft, saveState] = useSaveOnboardingDraftMutation()
  const [completeOnboarding, completeState] = useCompleteOnboardingMutation()
  const saving = saveState.isLoading || completeState.isLoading

  const applyAuthoritativeState = useCallback(
    (response: OnboardingStateResponse) => {
      setDraft(onboardingStateToDraft(response))
      setCurrentStep(onboardingStepToNumber(response.current_step))
      setMaxVisitedStep(onboardingStepToNumber(response.max_visited_step))
      setSaveError(null)
    },
    [],
  )

  useEffect(() => {
    if (standalone || hydrated || !onboardingQuery.data) {
      return
    }

    // One-time server hydration intentionally initializes the local editable draft.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    applyAuthoritativeState(onboardingQuery.data)
    setShowSuccess(showInitiallyCompleted && onboardingQuery.data.completed)
    setHydrated(true)
  }, [
    applyAuthoritativeState,
    hydrated,
    onboardingQuery.data,
    showInitiallyCompleted,
    standalone,
  ])

  const applyStandaloneNavigation = (
    nextDraft: SearchProfileFormValues,
    targetStep: SearchProfileFormStep,
  ) => {
    setDraft(nextDraft)
    setCurrentStep(targetStep)
    setMaxVisitedStep(
      (currentMax) => Math.max(currentMax, targetStep) as SearchProfileFormStep,
    )
    setSaveError(null)
  }

  const persistDraft = async (
    request: OnboardingDraftRequest,
  ): Promise<OnboardingStateResponse | null> => {
    if (requestPendingRef.current) {
      return null
    }

    requestPendingRef.current = true
    setSaveError(null)
    try {
      const response = await saveDraft(request).unwrap()
      applyAuthoritativeState(response)
      return response
    } catch (error) {
      setSaveError(
        getErrorMessage(error, 'Не удалось сохранить изменения. Попробуйте ещё раз.'),
      )
      return null
    } finally {
      requestPendingRef.current = false
    }
  }

  const handleFirstStepBack = () => {
    if (saving) {
      return
    }
    if (onBack) {
      onBack()
      return
    }
    if (window.history.length > 1) {
      window.history.back()
    }
  }

  const navigateBackward = async (target: SearchProfileFormStep) => {
    if (standalone) {
      applyStandaloneNavigation(draft, target)
      return
    }
    await persistDraft(
      backwardNavigationRequest(
        onboardingStepFromNumber(currentStep),
        onboardingStepFromNumber(target),
      ),
    )
  }

  const handleSpecialtyNavigation = async (
    targetStep: number,
    value: SpecialtyStepValue,
  ) => {
    if (targetStep < 1 || targetStep > maxVisitedStep || targetStep === currentStep) {
      return
    }
    const target = targetStep as SearchProfileFormStep
    if (target < currentStep) {
      await navigateBackward(target)
      return
    }
    const nextDraft = {
      ...draft,
      specializations: value.specializations,
      skills: value.skills,
    }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, target)
      return
    }
    await persistDraft(
      specialtyDraftRequest(value, onboardingStepFromNumber(target)),
    )
  }

  const handleSpecialtyContinue = async (value: SpecialtyStepValue) => {
    const nextDraft = {
      ...draft,
      specializations: value.specializations,
      skills: value.skills,
    }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, 2)
      return
    }
    await persistDraft(specialtyDraftRequest(value, 'WORK_FORMAT'))
  }

  const handleWorkFormatNavigation = async (
    targetStep: number,
    value: WorkFormatStepValue,
  ) => {
    if (targetStep < 1 || targetStep > maxVisitedStep || targetStep === currentStep) {
      return
    }
    const target = targetStep as SearchProfileFormStep
    if (target < currentStep) {
      await navigateBackward(target)
      return
    }
    if (value.workFormats.length === 0) {
      setSaveError('Выберите хотя бы один формат работы.')
      return
    }
    const nextDraft = { ...draft, workFormats: value.workFormats }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, target)
      return
    }
    await persistDraft(
      workFormatDraftRequest(value, onboardingStepFromNumber(target)),
    )
  }

  const handleWorkFormatContinue = async (value: WorkFormatStepValue) => {
    const nextDraft = { ...draft, workFormats: value.workFormats }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, 3)
      return
    }
    await persistDraft(workFormatDraftRequest(value, 'SALARY'))
  }

  const handleSalaryNavigation = async (
    targetStep: number,
    value: SalaryStepValue,
  ) => {
    if (targetStep < 1 || targetStep > maxVisitedStep || targetStep === currentStep) {
      return
    }
    const target = targetStep as SearchProfileFormStep
    if (target < currentStep) {
      await navigateBackward(target)
      return
    }
    if (value.mode === 'from' && value.amount === null) {
      setSaveError('Укажите корректную сумму зарплаты.')
      return
    }
    const nextDraft = { ...draft, salary: value }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, target)
      return
    }
    await persistDraft(salaryDraftRequest(value, onboardingStepFromNumber(target)))
  }

  const handleSalaryContinue = async (value: SalaryStepValue) => {
    const nextDraft = { ...draft, salary: value }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, 4)
      return
    }
    await persistDraft(salaryDraftRequest(value, 'LEVEL'))
  }

  const handleLevelNavigation = async (
    targetStep: number,
    value: LevelStepInitialValue,
  ) => {
    if (targetStep < 1 || targetStep > maxVisitedStep || targetStep === currentStep) {
      return
    }
    const target = targetStep as SearchProfileFormStep
    if (target < currentStep) {
      await navigateBackward(target)
      return
    }
    if (value.level === null) {
      setSaveError('Выберите уровень перед переходом.')
      return
    }
    const nextDraft = { ...draft, level: value.level }
    if (standalone) {
      applyStandaloneNavigation(nextDraft, target)
      return
    }
    await persistDraft(levelDraftRequest(value.level, onboardingStepFromNumber(target)))
  }

  const handleLevelComplete = async (value: LevelStepValue) => {
    const completedDraft = { ...draft, level: value.level }
    if (standalone) {
      setDraft(completedDraft)
      onComplete?.(completedDraft)
      return
    }
    const savedResponse = await persistDraft(levelDraftRequest(value.level, 'LEVEL'))
    if (!savedResponse) {
      return
    }

    requestPendingRef.current = true
    try {
      const response = await completeOnboarding().unwrap()
      applyAuthoritativeState(response)
      setShowSuccess(true)
      onComplete?.({
        ...onboardingStateToDraft(response),
        level: value.level,
      })
    } catch (error) {
      setSaveError(
        getErrorMessage(error, 'Не удалось завершить настройку. Попробуйте ещё раз.'),
      )
    } finally {
      requestPendingRef.current = false
    }
  }

  if (!standalone && !hydrated) {
    if (onboardingQuery.isError) {
      return (
        <StatusScreen
          title="Не удалось загрузить настройки"
          description={getErrorMessage(
            onboardingQuery.error,
            'Проверьте соединение и попробуйте ещё раз.',
          )}
          actionLabel="Повторить"
          onAction={() => void onboardingQuery.refetch()}
        />
      )
    }

    return (
      <StatusScreen
        loading
        title="Загружаем настройки"
        description="Восстанавливаем сохранённый прогресс."
      />
    )
  }

  if (showSuccess) {
    return (
      <StatusScreen
        title="Настройка завершена"
        description={completionDescription}
      />
    )
  }

  if (currentStep === 4 && draft.specializations.length > 0) {
    return (
      <LevelStep
        initialValue={{ level: draft.level }}
        maxVisitedStep={maxVisitedStep}
        saving={saving}
        saveError={saveError}
        summary={{
          specializations: draft.specializations,
          skills: draft.skills,
          workFormats: draft.workFormats,
          salary: draft.salary,
        }}
        onBack={(value) => void handleLevelNavigation(3, value)}
        onComplete={(value) => void handleLevelComplete(value)}
        onNavigateToStep={(step, value) =>
          void handleLevelNavigation(step, value)
        }
      />
    )
  }

  if (currentStep === 3) {
    return (
      <SalaryStep
        initialValue={draft.salary}
        maxVisitedStep={maxVisitedStep}
        saving={saving}
        saveError={saveError}
        onBack={(value) => void handleSalaryNavigation(2, value)}
        onContinue={(value) => void handleSalaryContinue(value)}
        onNavigateToStep={(step, value) =>
          void handleSalaryNavigation(step, value)
        }
      />
    )
  }

  if (currentStep === 2) {
    return (
      <WorkFormatStep
        initialValue={{ workFormats: draft.workFormats }}
        maxVisitedStep={maxVisitedStep}
        saving={saving}
        saveError={saveError}
        onBack={(value) => void handleWorkFormatNavigation(1, value)}
        onContinue={(value) => void handleWorkFormatContinue(value)}
        onNavigateToStep={(step, value) =>
          void handleWorkFormatNavigation(step, value)
        }
      />
    )
  }

  return (
    <SpecialtyStep
      initialValue={{
        specializations: draft.specializations,
        skills: draft.skills,
      }}
      maxVisitedStep={maxVisitedStep}
      saving={saving}
      saveError={saveError}
      onBack={handleFirstStepBack}
      onContinue={(value) => void handleSpecialtyContinue(value)}
      onNavigateToStep={(step, value) =>
        void handleSpecialtyNavigation(step, value)
      }
    />
  )
}
