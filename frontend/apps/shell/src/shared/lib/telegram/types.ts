export type TelegramColorScheme = 'light' | 'dark'

export interface TelegramWebAppUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  photo_url?: string
  is_premium?: boolean
}

export interface TelegramWebAppInitData {
  user?: TelegramWebAppUser
}

export interface TelegramThemeParams {
  bg_color?: string
  text_color?: string
  hint_color?: string
  link_color?: string
  button_color?: string
  button_text_color?: string
  secondary_bg_color?: string
}

export interface TelegramWebApp {
  readonly initData: string
  readonly initDataUnsafe: TelegramWebAppInitData
  readonly version: string
  readonly platform: string
  readonly colorScheme: TelegramColorScheme
  readonly themeParams: TelegramThemeParams

  ready(): void
  expand(): void
  close(): void
  isVersionAtLeast(version: string): boolean
}

export interface TelegramNamespace {
  WebApp: TelegramWebApp
}

declare global {
  interface Window {
    Telegram?: TelegramNamespace
  }
}
