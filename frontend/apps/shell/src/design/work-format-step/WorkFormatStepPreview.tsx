import { Box } from '@mui/material'

import { WorkFormatStep } from '@/features/onboarding/ui/WorkFormatStep'

const WorkFormatStepPreview = () => (
  <Box sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}>
    <WorkFormatStep
      initialValue={{ workFormats: ['remote', 'hybrid'] }}
      onContinue={(value) =>
        console.info('Work format preview completed.', value)
      }
    />
  </Box>
)

export default WorkFormatStepPreview
