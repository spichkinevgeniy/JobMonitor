import { Box } from '@mui/material'

import { LevelStep } from '@/features/onboarding/ui/LevelStep'

const LevelStepPreview = () => (
  <Box sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}>
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
)

export default LevelStepPreview
