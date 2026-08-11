import { Box } from '@mui/material'

import { SalaryStep } from '@/features/search-profile-form/ui/steps/SalaryStep'

const SalaryStepPreview = () => (
  <Box data-audit-case data-audit-id="salary-step--default">
    <Box
      data-audit-target
      data-audit-content-mode="none"
      sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}
    >
      <SalaryStep
        initialValue={{ mode: 'from', amount: 150000 }}
        onContinue={(value) => console.info('Salary preview completed.', value)}
      />
    </Box>
  </Box>
)

export default SalaryStepPreview
