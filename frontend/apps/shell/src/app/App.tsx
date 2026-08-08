import { useEffect } from 'react'

import { OnboardingPage } from '@/pages/onboarding'
import { initializeTelegramWebApp } from '@/shared/lib/telegram'

const App = () => {
  useEffect(() => {
    initializeTelegramWebApp()
  }, [])

  return <OnboardingPage />
}

export default App
