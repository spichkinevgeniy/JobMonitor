import AppsOutlinedIcon from '@mui/icons-material/AppsOutlined'
import BusinessOutlinedIcon from '@mui/icons-material/BusinessOutlined'
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined'
import SyncAltIcon from '@mui/icons-material/SyncAlt'
import { Box, Typography } from '@mui/material'
import { useState } from 'react'

import { BackButton } from '@/shared/ui/BackButton'
import { Button } from '@/shared/ui/Button'
import { ProgressStepper } from '@/shared/ui/ProgressStepper'
import { SelectionCard } from '@/shared/ui/SelectionCard'
import type {
  WorkFormatId,
  WorkFormatStepProps,
  WorkFormatStepValue,
} from './WorkFormatStep.types'

const workFormats = [
  {
    id: 'any',
    title: 'Любой формат',
    description: 'Показывать вакансии любого формата',
    icon: <AppsOutlinedIcon />,
  },
  {
    id: 'remote',
    title: 'Удалённо',
    description: 'Работа полностью из дома',
    icon: <HomeOutlinedIcon />,
  },
  {
    id: 'hybrid',
    title: 'Гибрид',
    description: 'Часть времени дома, часть в офисе',
    icon: <SyncAltIcon />,
  },
  {
    id: 'office',
    title: 'Офис',
    description: 'Работа из офиса компании',
    icon: <BusinessOutlinedIcon />,
  },
] as const

const isWorkFormatId = (workFormat: string): workFormat is WorkFormatId =>
  workFormats.some((supportedFormat) => supportedFormat.id === workFormat)

const getSupportedWorkFormats = (
  selectedFormats: WorkFormatId[] | undefined,
): WorkFormatId[] => {
  const supportedFormats = (selectedFormats ?? []).filter(isWorkFormatId)

  if (supportedFormats.includes('any')) {
    return ['any']
  }

  return [...new Set(supportedFormats)]
}

export const WorkFormatStep = ({
  initialValue,
  maxVisitedStep,
  onBack,
  onContinue,
  onNavigateToStep,
}: WorkFormatStepProps) => {
  const [selectedFormats, setSelectedFormats] = useState<WorkFormatId[]>(
    () => getSupportedWorkFormats(initialValue?.workFormats),
  )

  const toggleWorkFormat = (workFormat: WorkFormatId) => {
    setSelectedFormats((currentFormats) => {
      if (workFormat === 'any') {
        return currentFormats.includes('any') ? [] : ['any']
      }

      const concreteFormats = currentFormats.filter(
        (currentFormat) => currentFormat !== 'any',
      )

      return concreteFormats.includes(workFormat)
        ? concreteFormats.filter((currentFormat) => currentFormat !== workFormat)
        : [...concreteFormats, workFormat]
    })
  }

  const getCurrentValue = (): WorkFormatStepValue => ({
    workFormats: selectedFormats,
  })

  const handleContinue = () => {
    if (selectedFormats.length === 0) {
      return
    }

    onContinue?.(getCurrentValue())
  }

  const handleBack = () => {
    onBack?.(getCurrentValue())
  }

  const handleStepNavigation = (step: number) => {
    onNavigateToStep?.(step, getCurrentValue())
  }

  return (
    <Box
      component="section"
      aria-labelledby="work-format-step-title"
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
            currentStep={2}
            totalSteps={4}
            maxVisitedStep={maxVisitedStep}
            aria-label="Прогресс настройки поиска"
            onStepClick={handleStepNavigation}
          />
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography
            id="work-format-step-title"
            component="h1"
            sx={{
              color: 'text.primary',
              fontSize: 24,
              fontWeight: 700,
              lineHeight: '32px',
            }}
          >
            Как хотите работать?
          </Typography>
          <Typography
            sx={{
              mt: 0.75,
              color: 'text.secondary',
              fontSize: 15,
              lineHeight: '22px',
            }}
          >
            Выберите один или несколько подходящих форматов
          </Typography>
        </Box>
      </Box>

      <Box sx={{ flex: 1 }}>
        <Box
          role="group"
          aria-label="Формат работы"
          sx={{
            mt: 3,
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: 1.5,
          }}
        >
          {workFormats.map((workFormat) => (
            <SelectionCard
              key={workFormat.id}
              icon={workFormat.icon}
              title={workFormat.title}
              description={workFormat.description}
              selected={selectedFormats.includes(workFormat.id)}
              onClick={() => toggleWorkFormat(workFormat.id)}
            />
          ))}
        </Box>
      </Box>

      <Box
        component="footer"
        sx={{
          pt: 3,
          pb: 'calc(16px + env(safe-area-inset-bottom))',
        }}
      >
        <Button
          fullWidth
          disabled={selectedFormats.length === 0}
          onClick={handleContinue}
        >
          Продолжить
        </Button>
      </Box>
    </Box>
  )
}
