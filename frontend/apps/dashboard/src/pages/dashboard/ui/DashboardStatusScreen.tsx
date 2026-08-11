import { Box, ButtonBase, CircularProgress, Typography } from '@mui/material'
import { buttonBaseClasses } from '@mui/material/ButtonBase'
import { semanticColors } from '@jobmonitor/ui'

interface DashboardStatusScreenProps {
  title: string
  description: string
  loading?: boolean
  onRetry?: () => void
}

export const DashboardStatusScreen = ({
  title,
  description,
  loading = false,
  onRetry,
}: DashboardStatusScreenProps) => (
  <Box
    component="main"
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      maxWidth: 420,
      minHeight: '100dvh',
      mx: 'auto',
      px: 2,
      py: 'calc(32px + env(safe-area-inset-top))',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      bgcolor: 'background.default',
    }}
  >
    {loading && <CircularProgress size={28} sx={{ mb: 2 }} />}
    <Typography component="h1" sx={{ fontSize: 22, fontWeight: 700 }}>
      {title}
    </Typography>
    <Typography sx={{ mt: 1, color: 'text.secondary', fontSize: 15 }}>
      {description}
    </Typography>
    {onRetry && (
      <ButtonBase
        onClick={onRetry}
        sx={{
          minHeight: 44,
          mt: 2,
          px: 1.5,
          borderRadius: 2,
          color: semanticColors['color/text/brand'],
          fontSize: 14,
          fontWeight: 600,
          [`&.${buttonBaseClasses.focusVisible}`]: {
            outline: `2px solid ${semanticColors['color/border/brand']}`,
            outlineOffset: 2,
          },
        }}
      >
        Повторить
      </ButtonBase>
    )}
  </Box>
)
