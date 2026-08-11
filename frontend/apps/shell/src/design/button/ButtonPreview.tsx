import { Box } from '@mui/material'

import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { Button } from '@/shared/ui/Button'

const ButtonPreview = () => {
  return (
    <DesignPreviewPage
      title="Button"
      description="JobMonitor UI · Primary CTA · 48px"
      canvasWidth={820}
      columns={2}
    >
      <DesignPreviewCard title="Default">
        <Box data-audit-target sx={{ width: '100%' }}>
          <Button fullWidth>
            <span data-audit-content>Продолжить</span>
          </Button>
        </Box>
      </DesignPreviewCard>

      <DesignPreviewCard title="Disabled">
        <Box data-audit-target sx={{ width: '100%' }}>
          <Button fullWidth disabled>
            <span data-audit-content>Продолжить</span>
          </Button>
        </Box>
      </DesignPreviewCard>

      <DesignPreviewCard title="Loading">
        <Box
          data-audit-target
          data-audit-content-mode="none"
          sx={{ width: '100%' }}
        >
          <Button fullWidth loading>
            Продолжить
          </Button>
        </Box>
      </DesignPreviewCard>

      <DesignPreviewCard title="Hug Width">
        <Box data-audit-target sx={{ display: 'inline-flex', width: 'fit-content' }}>
          <Button>
            <span data-audit-content>Продолжить</span>
          </Button>
        </Box>
      </DesignPreviewCard>
    </DesignPreviewPage>
  )
}

export default ButtonPreview
