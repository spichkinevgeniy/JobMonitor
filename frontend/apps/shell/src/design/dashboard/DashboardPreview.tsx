import { Box } from '@mui/material'

import { DashboardPage } from '@/pages/dashboard'

const mockProfile = {
  specialization: 'Инженер по информационной безопасности',
  skills: [
    'React',
    'TypeScript',
    'Redux Toolkit',
    'JavaScript',
    'Next.js',
    'HTML',
    'CSS',
    'Sass',
    'Docker',
    'Git',
    'Webpack',
    'Vite',
  ],
  workFormat: 'Удалённо',
  salary: 'от 150 000 ₽',
  level: 'Junior+',
  searchActive: true,
}

const DashboardPreview = () => (
  <Box data-audit-case data-audit-id="dashboard--default">
    <Box
      data-audit-target
      data-audit-content-mode="none"
      sx={{ width: 390, maxWidth: '100%', mx: 'auto' }}
    >
      <DashboardPage
        profile={mockProfile}
        onEdit={() => undefined}
        onStatisticsClick={() => undefined}
      />
    </Box>
  </Box>
)

export default DashboardPreview
