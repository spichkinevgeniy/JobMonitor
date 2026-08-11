import { SearchProfileForm } from '@/features/search-profile-form'

import type { SettingsPageProps } from './SettingsPage.types'

export const SettingsPage = ({ onBack, onComplete }: SettingsPageProps) => (
  <SearchProfileForm
    showInitiallyCompleted={false}
    completionDescription="Изменения профиля сохранены."
    onBack={onBack}
    onComplete={onComplete}
  />
)
