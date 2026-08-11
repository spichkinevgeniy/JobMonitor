import type { TelegramWebApp } from './types'

export const getTelegramWebApp = (): TelegramWebApp | undefined => {
  if (typeof window === 'undefined') {
    return undefined
  }

  return window.Telegram?.WebApp
}

export const getTelegramInitData = (): string | undefined =>
  getTelegramWebApp()?.initData || undefined

export const initializeTelegramWebApp = (): TelegramWebApp | undefined => {
  const webApp = getTelegramWebApp()

  if (!webApp) {
    return undefined
  }

  webApp.ready()
  webApp.expand()

  return webApp
}

export const isTelegramEnvironment = (): boolean =>
  Boolean(getTelegramInitData())
