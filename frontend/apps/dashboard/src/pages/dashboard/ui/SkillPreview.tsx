import { Box } from '@mui/material'
import { Chip } from '@jobmonitor/ui'

interface SkillPreviewProps {
  skills: string[]
}

const maxVisibleSkills = 3

const chipSx = {
  maxWidth: 'calc(50% - 4px)',
  '& .MuiChip-label': {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
} as const

export const SkillPreview = ({ skills }: SkillPreviewProps) => {
  const visibleSkills = skills.slice(0, maxVisibleSkills)
  const hiddenSkillsCount = skills.length - visibleSkills.length

  if (visibleSkills.length === 0) {
    return null
  }

  return (
    <Box
      aria-label="Навыки"
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}
    >
      {visibleSkills.map((skill) => (
        <Chip key={skill} label={skill} sx={chipSx} />
      ))}
      {hiddenSkillsCount > 0 && (
        <Chip
          aria-label={`Ещё ${hiddenSkillsCount} навыков`}
          label={`+${hiddenSkillsCount}`}
          sx={chipSx}
        />
      )}
    </Box>
  )
}
