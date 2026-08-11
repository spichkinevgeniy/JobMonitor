import { Box } from '@mui/material'

import { LevelStep } from '@/features/search-profile-form/ui/steps/LevelStep'

const LevelStepPreview = () => (
  <Box data-audit-case data-audit-id="level-step--default">
    <Box
      data-audit-target
      data-audit-content-mode="none"
      sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}
    >
      <LevelStep
        initialValue={{ level: 'JUNIOR' }}
        summary={{
          specialty: 'Frontend',
          skills: ['React', 'TypeScript'],
          workFormats: ['remote', 'hybrid'],
          salary: {
            mode: 'from',
            amount: 150000,
          },
        }}
        onNavigateToStep={() => undefined}
      />
    </Box>
  </Box>
)

export default LevelStepPreview
