export interface DashboardProfile {
  specialization: string
  skills: string[]
  workFormat: string
  salary: string
  level: string
  searchActive: boolean
}

export interface DashboardPageProps {
  profile: DashboardProfile
  onEdit?: () => void
  onStatisticsClick?: () => void
}

export interface DashboardHeaderProps {
  onStatisticsClick?: () => void
}

export interface ActiveProfileCardProps {
  profile: DashboardProfile
  onEdit: () => void
}
