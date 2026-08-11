import { Box } from '@mui/material'

import { DashboardPage, type SearchProfile } from '../pages/dashboard'

const previewProfile: SearchProfile = {
  specialization: 'Frontend',
  skills: ['React', 'TypeScript'],
  workFormat: 'Удалённо',
  salary: 'от 150 000 ₽',
  level: 'Junior+',
  searchActive: true,
}

export const DashboardPreview = () => (
  <Box sx={{ minHeight: '100dvh', bgcolor: 'background.default' }}>
    <DashboardPage
      profile={previewProfile}
      onEdit={() => undefined}
      onStatisticsClick={() => undefined}
    />
  </Box>
)
