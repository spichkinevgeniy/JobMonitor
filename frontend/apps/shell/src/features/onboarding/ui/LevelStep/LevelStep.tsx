import BuildOutlinedIcon from '@mui/icons-material/BuildOutlined'
import CategoryOutlinedIcon from '@mui/icons-material/CategoryOutlined'
import HomeWorkOutlinedIcon from '@mui/icons-material/HomeWorkOutlined'
import PaymentsOutlinedIcon from '@mui/icons-material/PaymentsOutlined'
import { Box, Typography } from '@mui/material'
import ButtonBase, { buttonBaseClasses } from '@mui/material/ButtonBase'
import { styled } from '@mui/material/styles'
import { useState, type ReactNode } from 'react'

import { semanticColors } from '@/app/theme/foundations'
import { formatSalaryAmount } from '@/features/onboarding/lib'
import { BackButton } from '@/shared/ui/BackButton'
import { Button } from '@/shared/ui/Button'
import { Chip } from '@/shared/ui/Chip'
import { ProgressStepper } from '@/shared/ui/ProgressStepper'
import { levels } from './LevelStep.config'
import type {
  LevelId,
  LevelStepProps,
  LevelStepSummary,
} from './LevelStep.types'

const workFormatLabels = {
  any: 'Любой формат',
  remote: 'Удалённо',
  hybrid: 'Гибрид',
  office: 'Офис',
} as const

const specialtyLabels = {
  Frontend: 'Frontend',
  Backend: 'Backend',
  QA: 'QA',
  Analytics: 'Аналитика',
  'Infrastructure & DevOps': 'DevOps',
  Design: 'Дизайн',
} as const satisfies Record<LevelStepSummary['specialty'], string>

const SkillsToggle = styled(ButtonBase)({
  width: 'fit-content',
  minHeight: 36,
  marginTop: 4,
  paddingInline: 0,
  borderRadius: 8,
  color: semanticColors['color/text/brand'],
  fontSize: 13,
  fontWeight: 500,
  lineHeight: '18px',
  [`&.${buttonBaseClasses.focusVisible}`]: {
    outline: `2px solid ${semanticColors['color/border/brand']}`,
    outlineOffset: 2,
  },
})

interface SummaryRow {
  id: 'specialty' | 'skills' | 'workFormats' | 'salary'
  label: string
  value: string
  icon: ReactNode
}

const formatWorkFormats = (
  workFormats: LevelStepSummary['workFormats'],
): string =>
  workFormats.length > 0
    ? workFormats.map((workFormat) => workFormatLabels[workFormat]).join(' · ')
    : 'Не выбраны'

const formatSalary = (salary: LevelStepSummary['salary']): string =>
  salary.mode === 'from' && salary.amount !== null
    ? `От ${formatSalaryAmount(salary.amount)} ₽`
    : 'Не важна'

const getInitialLevel = (level: LevelId | null | undefined): LevelId | null =>
  levels.some((option) => option.id === level) ? (level ?? null) : null

export const LevelStep = ({
  initialValue,
  maxVisitedStep,
  summary,
  onBack,
  onComplete,
  onNavigateToStep,
}: LevelStepProps) => {
  const [selectedLevel, setSelectedLevel] = useState<LevelId | null>(() =>
    getInitialLevel(initialValue?.level),
  )
  const [skillsExpanded, setSkillsExpanded] = useState(false)

  const visibleSkills = skillsExpanded
    ? summary.skills
    : summary.skills.slice(0, 3)
  const hiddenSkillsCount = summary.skills.length - visibleSkills.length

  const handleBack = () => {
    onBack?.({ level: selectedLevel })
  }

  const handleStepNavigation = (step: number) => {
    onNavigateToStep?.(step, { level: selectedLevel })
  }

  const handleComplete = () => {
    if (!selectedLevel) {
      return
    }

    onComplete?.({ level: selectedLevel })
  }

  const summaryRows: SummaryRow[] = [
    {
      id: 'specialty',
      label: 'Специальность',
      value: specialtyLabels[summary.specialty],
      icon: <CategoryOutlinedIcon />,
    },
    {
      id: 'skills',
      label: 'Навыки',
      value: visibleSkills.length > 0 ? visibleSkills.join(' · ') : 'Не выбраны',
      icon: <BuildOutlinedIcon />,
    },
    {
      id: 'workFormats',
      label: 'Формат работы',
      value: formatWorkFormats(summary.workFormats),
      icon: <HomeWorkOutlinedIcon />,
    },
    {
      id: 'salary',
      label: 'Зарплата',
      value: formatSalary(summary.salary),
      icon: <PaymentsOutlinedIcon />,
    },
  ]

  return (
    <Box
      component="section"
      aria-labelledby="level-step-title"
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
            currentStep={4}
            totalSteps={4}
            maxVisitedStep={maxVisitedStep}
            aria-label="Прогресс настройки поиска"
            onStepClick={handleStepNavigation}
          />
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography
            id="level-step-title"
            component="h1"
            sx={{
              color: 'text.primary',
              fontSize: 24,
              fontWeight: 700,
              lineHeight: '32px',
            }}
          >
            Какой у вас уровень?
          </Typography>
          <Typography
            sx={{
              mt: 0.75,
              color: 'text.secondary',
              fontSize: 15,
              lineHeight: '22px',
            }}
          >
            Выберите уровень, который лучше всего описывает ваш опыт
          </Typography>
        </Box>
      </Box>

      <Box sx={{ flex: 1 }}>
        <Box
          role="group"
          aria-label="Уровень"
          sx={{
            mt: 3,
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          {levels.map((level) => (
            <Chip
              key={level.id}
              label={level.label}
              selected={selectedLevel === level.id}
              onClick={() => setSelectedLevel(level.id)}
            />
          ))}
        </Box>

        {selectedLevel && (
          <Box
            component="section"
            aria-labelledby="level-summary-title"
            sx={{
              mt: 3,
              border: 1,
              borderColor: 'divider',
              borderRadius: 4,
              bgcolor: 'background.paper',
              overflow: 'hidden',
            }}
          >
            <Typography
              id="level-summary-title"
              component="h2"
              sx={{
                px: 2,
                pt: 2,
                pb: 1,
                color: 'text.primary',
                fontSize: 16,
                fontWeight: 600,
                lineHeight: '24px',
              }}
            >
              Ваш выбор
            </Typography>

            <Box>
              {summaryRows.map((row, index) => (
                <Box
                  key={row.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 1.5,
                    px: 2,
                    py: 1.75,
                    borderTop: index === 0 ? 0 : 1,
                    borderColor: 'divider',
                  }}
                >
                  <Box
                    aria-hidden="true"
                    sx={{
                      width: 32,
                      height: 32,
                      flex: '0 0 32px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: 2,
                      bgcolor: semanticColors['color/bg/primary-subtle'],
                      color: semanticColors['color/icon/brand'],
                      '& .MuiSvgIcon-root': {
                        fontSize: 20,
                      },
                    }}
                  >
                    {row.icon}
                  </Box>

                  <Box sx={{ minWidth: 0, flex: 1 }}>
                    <Typography
                      sx={{
                        color: 'text.secondary',
                        fontSize: 13,
                        lineHeight: '18px',
                      }}
                    >
                      {row.label}
                    </Typography>
                    <Typography
                      sx={{
                        mt: 0.25,
                        color: 'text.primary',
                        fontSize: 15,
                        fontWeight: 600,
                        lineHeight: '20px',
                        overflowWrap: 'anywhere',
                        whiteSpace: 'normal',
                      }}
                    >
                      {row.value}
                    </Typography>

                    {row.id === 'skills' && summary.skills.length > 3 && (
                      <SkillsToggle
                        aria-expanded={skillsExpanded}
                        onClick={() =>
                          setSkillsExpanded((isExpanded) => !isExpanded)
                        }
                      >
                        {skillsExpanded
                          ? 'Свернуть'
                          : `+ ещё ${hiddenSkillsCount}`}
                      </SkillsToggle>
                    )}
                  </Box>
                </Box>
              ))}
            </Box>
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
        <Button
          fullWidth
          disabled={selectedLevel === null}
          onClick={handleComplete}
        >
          Начать поиск
        </Button>
      </Box>
    </Box>
  )
}
