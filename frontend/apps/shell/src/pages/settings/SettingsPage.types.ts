import type { CompletedSearchProfileValue } from '@/features/search-profile-form'

export interface SettingsPageProps {
  onBack?: () => void
  onComplete?: (value: CompletedSearchProfileValue) => void
}
