import { Box } from '@mui/material'

import { WorkFormatStep } from '@/features/search-profile-form/ui/steps/WorkFormatStep'

const WorkFormatStepPreview = () => (
  <Box data-audit-case data-audit-id="work-format-step--default">
    <Box
      data-audit-target
      data-audit-content-mode="none"
      sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}
    >
      <WorkFormatStep
        initialValue={{ workFormats: ['remote', 'hybrid'] }}
        onContinue={(value) =>
          console.info('Work format preview completed.', value)
        }
      />
    </Box>
  </Box>
)

export default WorkFormatStepPreview
