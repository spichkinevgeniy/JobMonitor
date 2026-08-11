import { Box } from '@mui/material'

import type { DashboardPageProps } from './DashboardPage.types'
import { ActiveProfileCard } from './ui/ActiveProfileCard'
import { DashboardHeader } from './ui/DashboardHeader'
import { VacanciesSection } from './ui/VacanciesSection'

export const DashboardPage = ({
  profile,
  onEdit,
  onStatisticsClick,
}: DashboardPageProps) => (
  <Box
    component="main"
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      maxWidth: 420,
      minHeight: '100dvh',
      mx: 'auto',
      px: 2,
      pt: 'calc(12px + env(safe-area-inset-top))',
      pb: 'calc(20px + env(safe-area-inset-bottom))',
      bgcolor: 'background.default',
    }}
  >
    <DashboardHeader onStatisticsClick={onStatisticsClick} />

    <Box sx={{ mt: 2.5 }}>
      <ActiveProfileCard
        profile={profile}
        onEdit={onEdit}
      />
    </Box>

    <Box sx={{ mt: 3 }}>
      <VacanciesSection />
    </Box>
  </Box>
)
