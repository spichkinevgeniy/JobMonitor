import type { SearchProfile } from './model/types'

export interface DashboardPageProps {
  profile: SearchProfile
  onEdit: () => void
  onStatisticsClick: () => void
}
