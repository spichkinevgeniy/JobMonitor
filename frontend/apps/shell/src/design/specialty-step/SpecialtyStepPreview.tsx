import { Box } from '@mui/material'

import { OnboardingPage } from '@/pages/onboarding'

const SpecialtyStepPreview = () => (
  <Box sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}>
    <OnboardingPage
      initialValue={{
        specialty: 'Frontend',
        skills: ['React', 'TypeScript'],
      }}
    />
  </Box>
)

export default SpecialtyStepPreview
