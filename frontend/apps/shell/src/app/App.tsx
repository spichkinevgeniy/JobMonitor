import { useEffect } from 'react'

import { OnboardingPage } from '@/pages/onboarding'
import { SettingsPage } from '@/pages/settings'
import { initializeTelegramWebApp } from '@jobmonitor/telegram'

import { openDashboard } from './navigation'

const isSettingsMode = () =>
  typeof window !== 'undefined' &&
  new URLSearchParams(window.location.search).get('mode') === 'settings'

const App = () => {
  useEffect(() => {
    initializeTelegramWebApp()
  }, [])

  return isSettingsMode() ? (
    <SettingsPage onComplete={openDashboard} />
  ) : (
    <OnboardingPage onComplete={openDashboard} />
  )
}

export default App
