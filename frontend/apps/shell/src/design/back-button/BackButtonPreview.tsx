import { Box } from '@mui/material'

import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { BackButton } from '@/shared/ui/BackButton'

const BackButtonPreview = () => {
  return (
    <DesignPreviewPage
      title="BackButton"
      description="JobMonitor UI · Navigation control · 44px"
    >
      <DesignPreviewCard title="Default">
        <Box data-audit-target sx={{ display: 'inline-flex', width: 'fit-content' }}>
          <BackButton label={<span data-audit-content>Назад</span>} />
        </Box>
      </DesignPreviewCard>
    </DesignPreviewPage>
  )
}

export default BackButtonPreview
