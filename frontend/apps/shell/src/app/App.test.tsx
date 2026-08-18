import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'

const { initializeTelegramWebAppMock, openDashboardMock } = vi.hoisted(() => ({
  initializeTelegramWebAppMock: vi.fn(),
  openDashboardMock: vi.fn(),
}))

vi.mock('@jobmonitor/telegram', () => ({
  initializeTelegramWebApp: initializeTelegramWebAppMock,
}))

vi.mock('@/pages/onboarding', () => ({
  OnboardingPage: ({
    initialValue,
  }: {
    initialValue?: { specializations: string[]; skills: string[] }
  }) => (
    <div>
      {initialValue ? 'Standalone onboarding preview' : 'Onboarding page'}
    </div>
  ),
}))

vi.mock('@/pages/settings', () => ({
  SettingsPage: ({ onComplete }: { onComplete?: () => void }) => (
    <button type="button" onClick={onComplete}>
      Save settings
    </button>
  ),
}))

vi.mock('./navigation', () => ({
  openDashboard: openDashboardMock,
}))

import App from './App'

beforeEach(() => {
  initializeTelegramWebAppMock.mockReset()
  openDashboardMock.mockReset()
})

it('renders normal onboarding without settings mode', () => {
  window.history.replaceState({}, '', '/miniapp/react/?mode=onboarding')

  render(<App />)

  expect(screen.getByText('Onboarding page')).toBeInTheDocument()
  expect(initializeTelegramWebAppMock).toHaveBeenCalledOnce()
})

it('renders a standalone browser preview without Telegram initialization', () => {
  window.history.replaceState({}, '', '/miniapp/react/?mode=preview')

  render(<App />)

  expect(screen.getByText('Standalone onboarding preview')).toBeInTheDocument()
  expect(initializeTelegramWebAppMock).not.toHaveBeenCalled()
})

it('returns to Dashboard after settings completion', async () => {
  window.history.replaceState({}, '', '/miniapp/react/?mode=settings')
  const user = userEvent.setup()

  render(<App />)
  await user.click(screen.getByRole('button', { name: 'Save settings' }))

  expect(openDashboardMock).toHaveBeenCalledOnce()
})
