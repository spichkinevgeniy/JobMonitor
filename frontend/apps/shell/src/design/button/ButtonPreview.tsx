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
        <Button fullWidth>Продолжить</Button>
      </DesignPreviewCard>

      <DesignPreviewCard title="Disabled">
        <Button fullWidth disabled>
          Продолжить
        </Button>
      </DesignPreviewCard>

      <DesignPreviewCard title="Loading">
        <Button fullWidth loading>
          Продолжить
        </Button>
      </DesignPreviewCard>

      <DesignPreviewCard title="Hug Width">
        <Box sx={{ width: 'fit-content' }}>
          <Button>Продолжить</Button>
        </Box>
      </DesignPreviewCard>
    </DesignPreviewPage>
  )
}

export default ButtonPreview
