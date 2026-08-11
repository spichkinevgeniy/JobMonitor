import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { semanticColors } from '@jobmonitor/ui'
import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { ProgressStepper } from '@/shared/ui/ProgressStepper'

interface PreviewStateProps {
  label: string
  children: ReactNode
}

const PreviewState = ({ label, children }: PreviewStateProps) => (
  <Box
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      height: 128,
      display: 'grid',
      gridTemplateRows: 'auto 1fr',
      gap: 1,
      p: 2,
      border: `1px solid ${semanticColors['color/border/default']}`,
      borderRadius: '12px',
      backgroundColor: semanticColors['color/bg/surface'],
    }}
  >
    <Typography sx={{ color: 'text.secondary', fontSize: 13, fontWeight: 600 }}>
      {label}
    </Typography>
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Box
        data-audit-target
        data-audit-content-mode="none"
        sx={{ width: '100%' }}
      >
        {children}
      </Box>
    </Box>
  </Box>
)

const ProgressStepperPreview = () => (
  <DesignPreviewPage
    title="ProgressStepper"
    description="JobMonitor UI · Onboarding progress · 4 steps"
    canvasWidth={720}
    columns={2}
  >
    <DesignPreviewCard title="Step 1">
      <PreviewState label="Step 1">
        <ProgressStepper currentStep={1} totalSteps={4} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Step 2">
      <PreviewState label="Step 2">
        <ProgressStepper currentStep={2} totalSteps={4} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Step 3">
      <PreviewState label="Step 3">
        <ProgressStepper currentStep={3} totalSteps={4} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Step 4">
      <PreviewState label="Step 4">
        <ProgressStepper currentStep={4} totalSteps={4} />
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
)

export default ProgressStepperPreview
