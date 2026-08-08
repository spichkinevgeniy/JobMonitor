import BarChartIcon from '@mui/icons-material/BarChart'
import BrushOutlinedIcon from '@mui/icons-material/BrushOutlined'
import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined'
import CloudQueueIcon from '@mui/icons-material/CloudQueue'
import CodeIcon from '@mui/icons-material/Code'
import SearchIcon from '@mui/icons-material/Search'
import StorageIcon from '@mui/icons-material/Storage'
import { Box, Typography } from '@mui/material'
import { useState } from 'react'

import { BackButton } from '@/shared/ui/BackButton'
import { Button } from '@/shared/ui/Button'
import { Chip } from '@/shared/ui/Chip'
import { ProgressStepper } from '@/shared/ui/ProgressStepper'
import { SelectionCard } from '@/shared/ui/SelectionCard'
import { TextField } from '@/shared/ui/TextField'
import type {
  Skill,
  SpecialtyId,
  SpecialtyStepProps,
  SpecialtyStepValue,
} from './SpecialtyStep.types'

const specialties = [
  {
    id: 'Frontend',
    title: 'Frontend',
    description: 'Вёрстка и работа с интерфейсами',
    icon: <CodeIcon />,
  },
  {
    id: 'Backend',
    title: 'Backend',
    description: 'Серверная часть и API',
    icon: <StorageIcon />,
  },
  {
    id: 'QA',
    title: 'QA',
    description: 'Тестирование и контроль качества',
    icon: <BugReportOutlinedIcon />,
  },
  {
    id: 'Analytics',
    title: 'Аналитика',
    description: 'Работа с данными и метриками',
    icon: <BarChartIcon />,
  },
  {
    id: 'Infrastructure & DevOps',
    title: 'DevOps',
    description: 'Инфраструктура и автоматизация',
    icon: <CloudQueueIcon />,
  },
  {
    id: 'Design',
    title: 'Дизайн',
    description: 'Интерфейсы и пользовательский опыт',
    icon: <BrushOutlinedIcon />,
  },
] as const

const skills = [
  'React',
  'TypeScript',
  'JavaScript',
  'Node.js',
  'Python',
  'SQL',
  'Docker',
] as const

export const isSpecialtyId = (
  specialty: string | null | undefined,
): specialty is SpecialtyId =>
  specialties.some((item) => item.id === specialty)

export const isSkill = (skill: string): skill is Skill =>
  skills.some((supportedSkill) => supportedSkill === skill)

const getSupportedSpecialty = (
  specialty: string | null | undefined,
): SpecialtyId | null => (isSpecialtyId(specialty) ? specialty : null)

const getSupportedSkills = (selectedSkills: string[] | undefined): Skill[] =>
  (selectedSkills ?? []).filter(isSkill)

export const SpecialtyStep = ({
  initialValue,
  maxVisitedStep,
  onBack,
  onContinue,
  onNavigateToStep,
}: SpecialtyStepProps) => {
  const [selectedSpecialty, setSelectedSpecialty] = useState<SpecialtyId | null>(
    () => getSupportedSpecialty(initialValue?.specialty),
  )
  const [selectedSkills, setSelectedSkills] = useState<Skill[]>(
    () => getSupportedSkills(initialValue?.skills),
  )
  const [skillQuery, setSkillQuery] = useState('')

  const normalizedQuery = skillQuery.trim().toLowerCase()
  const filteredSkills = skills.filter((skill) =>
    skill.toLowerCase().includes(normalizedQuery),
  )

  const toggleSkill = (skill: Skill) => {
    setSelectedSkills((currentSkills) =>
      currentSkills.includes(skill)
        ? currentSkills.filter((item) => item !== skill)
        : [...currentSkills, skill],
    )
  }

  const handleContinue = () => {
    if (!selectedSpecialty) {
      return
    }

    onContinue?.({
      specialty: selectedSpecialty,
      skills: selectedSkills,
    })
  }

  const handleStepNavigation = (step: number) => {
    if (!selectedSpecialty) {
      return
    }

    onNavigateToStep?.(step, {
      specialty: selectedSpecialty,
      skills: selectedSkills,
    })
  }

  return (
    <Box
      component="section"
      aria-labelledby="specialty-step-title"
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
        <BackButton onClick={onBack} />

        <Box sx={{ mt: 1, px: 1 }}>
          <ProgressStepper
            currentStep={1}
            totalSteps={4}
            maxVisitedStep={maxVisitedStep}
            aria-label="Прогресс настройки поиска"
            onStepClick={onNavigateToStep ? handleStepNavigation : undefined}
          />
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography
            id="specialty-step-title"
            component="h1"
            sx={{
              color: 'text.primary',
              fontSize: 24,
              fontWeight: 700,
              lineHeight: '32px',
            }}
          >
            Кем хотите работать?
          </Typography>
          <Typography
            sx={{
              mt: 0.75,
              color: 'text.secondary',
              fontSize: 15,
              lineHeight: '22px',
            }}
          >
            Выберите специальность и ключевые навыки
          </Typography>
        </Box>
      </Box>

      <Box sx={{ flex: 1 }}>
        <Box
          role="group"
          aria-label="Специальности"
          sx={{
            mt: 3,
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: 1.5,
            '@media (max-width: 374px)': {
              gridTemplateColumns: '1fr',
            },
          }}
        >
          {specialties.map((specialty) => (
            <SelectionCard
              key={specialty.id}
              icon={specialty.icon}
              title={specialty.title}
              description={specialty.description}
              selected={selectedSpecialty === specialty.id}
              onClick={() => setSelectedSpecialty(specialty.id)}
            />
          ))}
        </Box>

        <Box component="section" aria-labelledby="skills-title" sx={{ mt: 3 }}>
          <Typography
            id="skills-title"
            component="h2"
            sx={{
              color: 'text.primary',
              fontSize: 16,
              fontWeight: 600,
              lineHeight: '24px',
            }}
          >
            Ключевые навыки
          </Typography>

          <Box sx={{ mt: 1.5 }}>
            <TextField
              value={skillQuery}
              onChange={(event) => setSkillQuery(event.target.value)}
              startAdornment={<SearchIcon />}
              placeholder="Найдите навык"
              aria-label="Поиск навыков"
            />
          </Box>

          <Box
            role="group"
            aria-label="Навыки"
            sx={{
              mt: 1.5,
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1,
            }}
          >
            {filteredSkills.map((skill) => (
              <Chip
                key={skill}
                label={skill}
                selected={selectedSkills.includes(skill)}
                onClick={() => toggleSkill(skill)}
              />
            ))}
          </Box>

          {filteredSkills.length === 0 && (
            <Typography
              role="status"
              sx={{ mt: 1.5, color: 'text.secondary', fontSize: 14 }}
            >
              Навыки не найдены
            </Typography>
          )}
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
          disabled={!selectedSpecialty}
          onClick={handleContinue}
        >
          Продолжить
        </Button>
      </Box>
    </Box>
  )
}
