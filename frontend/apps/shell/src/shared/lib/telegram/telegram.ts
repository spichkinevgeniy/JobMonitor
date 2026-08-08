import type { TelegramWebApp } from './types'

export function getTelegramWebApp(): TelegramWebApp | undefined {
  if (typeof window === 'undefined') {
    return undefined
  }

  return window.Telegram?.WebApp
}

export function initializeTelegramWebApp(): TelegramWebApp | undefined {
  const webApp = getTelegramWebApp()

  if (!webApp) {
    return undefined
  }

  webApp.ready()
  webApp.expand()

  return webApp
}

export function isTelegramEnvironment(): boolean {
  return Boolean(getTelegramWebApp()?.initData)
}
