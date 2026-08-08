import { Box, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

interface DesignPreviewPageProps {
  title: string
  description: string
  children: ReactNode
  canvasWidth?: number
  columns?: 1 | 2
}

export const DesignPreviewPage = ({
  title,
  description,
  children,
  canvasWidth = 440,
  columns = 1,
}: DesignPreviewPageProps) => {
  return (
    <Box
      component="main"
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        px: 2,
        py: 4,
      }}
    >
      <Box
        sx={{
          boxSizing: 'border-box',
          width: canvasWidth,
          maxWidth: '100%',
          mx: 'auto',
          p: 3,
        }}
      >
        <Stack spacing={3}>
          <Box component="header">
            <Typography
              component="h1"
              sx={{ color: 'text.primary', fontSize: 24, fontWeight: 700 }}
            >
              {title}
            </Typography>
            <Typography
              sx={{ mt: 0.5, color: 'text.secondary', fontSize: 14 }}
            >
              {description}
            </Typography>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns:
                columns === 2 ? 'repeat(2, minmax(0, 1fr))' : '1fr',
              gap: 2,
            }}
          >
            {children}
          </Box>
        </Stack>
      </Box>
    </Box>
  )
}

interface DesignPreviewCardProps {
  title: string
  children: ReactNode
}

export const DesignPreviewCard = ({
  title,
  children,
}: DesignPreviewCardProps) => {
  return (
    <Box
  sx={{
    width: 328,
    maxWidth: '100%',
    mx: 'auto',
    display: 'flex',
    justifyContent: 'center',
  }}
>
  {children}
</Box>
  )
}
