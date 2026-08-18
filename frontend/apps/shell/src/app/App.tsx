import { useEffect } from 'react'

import { OnboardingPage } from '@/pages/onboarding'
import { SettingsPage } from '@/pages/settings'
import { initializeTelegramWebApp } from '@jobmonitor/telegram'

import { openDashboard } from './navigation'

const getMode = () =>
  typeof window === 'undefined'
    ? null
    : new URLSearchParams(window.location.search).get('mode')

const App = () => {
  const mode = getMode()
  const isPreviewMode = mode === 'preview'

  useEffect(() => {
    if (isPreviewMode) {
      return
    }
    initializeTelegramWebApp()
  }, [isPreviewMode])

  if (isPreviewMode) {
    return (
      <OnboardingPage
        initialValue={{
          specializations: [],
          skills: [],
        }}
      />
    )
  }

  return mode === 'settings' ? (
    <SettingsPage onComplete={openDashboard} />
  ) : (
    <OnboardingPage onComplete={openDashboard} />
  )
}

export default App
