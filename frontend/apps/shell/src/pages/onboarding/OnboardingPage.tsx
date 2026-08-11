import { SearchProfileForm } from '@/features/search-profile-form'

import type { OnboardingPageProps } from './OnboardingPage.types'

export const OnboardingPage = ({
  initialValue,
  onBack,
  onComplete,
}: OnboardingPageProps) => (
  <SearchProfileForm
    initialValues={initialValue}
    onBack={onBack}
    onComplete={onComplete}
  />
)
