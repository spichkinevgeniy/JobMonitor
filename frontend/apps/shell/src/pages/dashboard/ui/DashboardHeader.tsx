import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import BarChartOutlinedIcon from '@mui/icons-material/BarChartOutlined'
import WorkOutlineRoundedIcon from '@mui/icons-material/WorkOutlineRounded'
import { Box, ButtonBase, Typography } from '@mui/material'
import { buttonBaseClasses } from '@mui/material/ButtonBase'

import { semanticColors } from '@jobmonitor/ui'
import type { DashboardHeaderProps } from '../DashboardPage.types'

export const DashboardHeader = ({
  onStatisticsClick,
}: DashboardHeaderProps) => (
  <Box
    component="header"
    sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
  >
    <Box sx={{ minWidth: 0, flex: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box
        aria-hidden="true"
        sx={{
          width: 36,
          height: 36,
          flex: '0 0 36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 2.5,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          '& .MuiSvgIcon-root': { fontSize: 20 },
        }}
      >
        <WorkOutlineRoundedIcon />
      </Box>

      <Typography
        component="h1"
        sx={{
          minWidth: 0,
          flex: 1,
          color: 'text.primary',
          fontSize: 19,
          fontWeight: 700,
          lineHeight: '26px',
        }}
      >
        JobMonitor
      </Typography>

    </Box>

    <ButtonBase
      aria-label="Открыть статистику"
      onClick={onStatisticsClick}
      sx={{
        minHeight: 36,
        flexShrink: 0,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.5,
        px: 1,
        borderRadius: 2,
        color: semanticColors['color/text/brand'],
        fontSize: 13,
        fontWeight: 600,
        lineHeight: '18px',
        '&:hover': {
          bgcolor: semanticColors['color/bg/primary-subtle'],
        },
        [`&.${buttonBaseClasses.focusVisible}`]: {
          outline: `2px solid ${semanticColors['color/border/brand']}`,
          outlineOffset: 2,
        },
        '& .MuiSvgIcon-root': {
          color: semanticColors['color/icon/brand'],
          fontSize: 17,
        },
      }}
    >
      <BarChartOutlinedIcon aria-hidden="true" />
      Статистика
      <ArrowForwardRoundedIcon aria-hidden="true" />
    </ButtonBase>
  </Box>
)
