import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { semanticColors } from '@/app/theme/foundations'
import { Chip } from '@/shared/ui/Chip'
import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'

interface PreviewStateProps {
  label: string
  children: ReactNode
  height?: number
}

const PreviewState = ({ label, children, height = 180 }: PreviewStateProps) => (
  <Box
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      height,
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
    <Box
      sx={{
        minWidth: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {children}
    </Box>
  </Box>
)

const ChipPreview = () => (
  <DesignPreviewPage
    title="Chip"
    description="JobMonitor UI · Selectable skill · 32px"
    canvasWidth={560}
    columns={2}
  >
    <DesignPreviewCard title="Default">
      <PreviewState label="Default">
        <Chip label="JavaScript" selected={false} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Selected">
      <PreviewState label="Selected">
        <Chip label="React" selected />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Disabled">
      <PreviewState label="Disabled">
        <Chip label="Docker" selected={false} disabled />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Skills wrap">
      <PreviewState label="Skills wrap" height={320}>
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 1,
          }}
        >
          <Chip label="React" selected />
          <Chip label="TypeScript" selected />
          <Chip label="JavaScript" selected={false} />
          <Chip label="Node.js" selected={false} />
          <Chip label="Python" selected={false} />
          <Chip label="SQL" selected={false} />
          <Chip label="Docker" selected={false} />
        </Box>
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
)

export default ChipPreview
