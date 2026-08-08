import CloseIcon from '@mui/icons-material/Close'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { semanticColors } from '@/app/theme/foundations'
import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { IconButton } from '@/shared/ui/IconButton'

interface PreviewStateProps {
  label: string
  children: ReactNode
}

const PreviewState = ({ label, children }: PreviewStateProps) => (
  <Box
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      height: 132,
      display: 'grid',
      gridTemplateRows: 'auto 1fr',
      gap: 1,
      p: 2,
      border: `1px solid ${semanticColors['color/border/default']}`,
      borderRadius: '12px',
      backgroundColor: semanticColors['color/bg/surface'],
      '& .IconButtonPreview-forceHover': {
        backgroundColor: semanticColors['color/bg/subtle'],
      },
    }}
  >
    <Typography sx={{ color: 'text.secondary', fontSize: 13, fontWeight: 600 }}>
      {label}
    </Typography>
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {children}
    </Box>
  </Box>
)

const IconButtonPreview = () => (
  <DesignPreviewPage
    title="IconButton"
    description="JobMonitor UI · Icon-only action · 44px"
    canvasWidth={400}
    columns={2}
  >
    <DesignPreviewCard title="Default">
      <PreviewState label="Default">
        <IconButton aria-label="Открыть меню">
          <MoreVertIcon />
        </IconButton>
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Hover">
      <PreviewState label="Hover">
        <IconButton
          aria-label="Открыть меню"
          className="IconButtonPreview-forceHover"
        >
          <MoreVertIcon />
        </IconButton>
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Close">
      <PreviewState label="Close">
        <IconButton aria-label="Закрыть">
          <CloseIcon />
        </IconButton>
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Disabled">
      <PreviewState label="Disabled">
        <IconButton aria-label="Открыть меню" disabled>
          <MoreVertIcon />
        </IconButton>
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
)

export default IconButtonPreview
