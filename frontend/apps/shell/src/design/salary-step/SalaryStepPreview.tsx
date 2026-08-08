import { Box } from '@mui/material'

import { SalaryStep } from '@/features/onboarding/ui/SalaryStep'

const SalaryStepPreview = () => (
  <Box sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}>
    <SalaryStep
      initialValue={{ mode: 'from', amount: 150000 }}
      onContinue={(value) => console.info('Salary preview completed.', value)}
    />
  </Box>
)

export default SalaryStepPreview
