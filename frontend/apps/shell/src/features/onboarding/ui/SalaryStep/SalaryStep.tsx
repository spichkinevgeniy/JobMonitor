import MoneyOffOutlinedIcon from '@mui/icons-material/MoneyOffOutlined'
import PaymentsOutlinedIcon from '@mui/icons-material/PaymentsOutlined'
import { Box, Typography } from '@mui/material'
import { useState } from 'react'

import { formatSalaryAmount } from '@/features/onboarding/lib'
import { BackButton } from '@/shared/ui/BackButton'
import { Button } from '@/shared/ui/Button'
import { ProgressStepper } from '@/shared/ui/ProgressStepper'
import { SelectionCard } from '@/shared/ui/SelectionCard'
import { TextField } from '@/shared/ui/TextField'
import type {
  SalaryMode,
  SalaryStepProps,
  SalaryStepValue,
} from './SalaryStep.types'

const getInitialMode = (initialValue: SalaryStepValue | undefined): SalaryMode =>
  initialValue?.mode === 'from' ? 'from' : 'any'

const getInitialSalaryInput = (
  initialValue: SalaryStepValue | undefined,
): string =>
  initialValue?.mode === 'from' &&
  typeof initialValue.amount === 'number' &&
  Number.isFinite(initialValue.amount) &&
  initialValue.amount > 0
    ? String(Math.trunc(initialValue.amount))
    : ''

const parseSalary = (digits: string): number | null => {
  if (!digits) {
    return null
  }

  const amount = Number(digits)

  return Number.isFinite(amount) && amount > 0 ? amount : null
}

export const SalaryStep = ({
  initialValue,
  maxVisitedStep,
  onBack,
  onContinue,
  onNavigateToStep,
}: SalaryStepProps) => {
  const [mode, setMode] = useState<SalaryMode>(() =>
    getInitialMode(initialValue),
  )
  const [salaryInput, setSalaryInput] = useState(() =>
    getInitialSalaryInput(initialValue),
  )

  const amount = parseSalary(salaryInput)
  const canContinue = mode === 'any' || amount !== null

  const getCurrentValue = (): SalaryStepValue => ({
    mode,
    amount: mode === 'from' ? amount : null,
  })

  const handleBack = () => {
    onBack?.(getCurrentValue())
  }

  const handleStepNavigation = (step: number) => {
    onNavigateToStep?.(step, getCurrentValue())
  }

  const handleContinue = () => {
    if (!canContinue) {
      return
    }

    onContinue?.(getCurrentValue())
  }

  return (
    <Box
      component="section"
      aria-labelledby="salary-step-title"
      sx={{
        boxSizing: 'border-box',
        width: '100%',
        maxWidth: 420,
        minHeight: '100dvh',
        mx: 'auto',
        px: 2,
        pt: 'calc(8px + env(safe-area-inset-top))',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      <Box component="header">
        <BackButton onClick={handleBack} />

        <Box sx={{ mt: 1, px: 1 }}>
          <ProgressStepper
            currentStep={3}
            totalSteps={4}
            maxVisitedStep={maxVisitedStep}
            aria-label="Прогресс настройки поиска"
            onStepClick={handleStepNavigation}
          />
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography
            id="salary-step-title"
            component="h1"
            sx={{
              color: 'text.primary',
              fontSize: 24,
              fontWeight: 700,
              lineHeight: '32px',
            }}
          >
            Какую зарплату ищете?
          </Typography>
          <Typography
            sx={{
              mt: 0.75,
              color: 'text.secondary',
              fontSize: 15,
              lineHeight: '22px',
            }}
          >
            Укажите минимальную зарплату или пропустите этот фильтр
          </Typography>
        </Box>
      </Box>

      <Box sx={{ flex: 1 }}>
        <Box
          role="group"
          aria-label="Фильтр по зарплате"
          sx={{
            mt: 3,
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: 1.5,
          }}
        >
          <SelectionCard
            icon={<MoneyOffOutlinedIcon />}
            title="Зарплата не важна"
            description="Не фильтровать вакансии по зарплате"
            selected={mode === 'any'}
            onClick={() => setMode('any')}
          />
          <SelectionCard
            icon={<PaymentsOutlinedIcon />}
            title="От указанной суммы"
            description="Показывать вакансии не ниже указанной суммы"
            selected={mode === 'from'}
            onClick={() => setMode('from')}
          />
        </Box>

        {mode === 'from' && (
          <Box sx={{ mt: 3 }}>
            <TextField
              label="Сумма в месяц, ₽"
              type="text"
              inputMode="numeric"
              value={formatSalaryAmount(salaryInput)}
              onChange={(event) =>
                setSalaryInput(event.target.value.replace(/\D/g, ''))
              }
              endAdornment="₽"
              helperText="Укажите сумму до вычета налогов"
            />
          </Box>
        )}
      </Box>

      <Box
        component="footer"
        sx={{
          pt: 3,
          pb: 'calc(16px + env(safe-area-inset-bottom))',
        }}
      >
        <Button fullWidth disabled={!canContinue} onClick={handleContinue}>
          Продолжить
        </Button>
      </Box>
    </Box>
  )
}
