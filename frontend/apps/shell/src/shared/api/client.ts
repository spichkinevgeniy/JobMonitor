import { getTelegramWebApp } from '@/shared/lib/telegram'
import { ApiError, TelegramAuthorizationError } from './errors'

export interface TelegramGetOptions {
  signal?: AbortSignal
}

export async function telegramGet<T>(
  path: string,
  options: TelegramGetOptions = {},
): Promise<T> {
  const initData = getTelegramWebApp()?.initData

  if (!initData) {
    throw new TelegramAuthorizationError()
  }

  const response = await fetch(path, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'X-Telegram-Init-Data': initData,
    },
    signal: options.signal,
  })
  const payload: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(getErrorMessage(payload), response.status)
  }

  return payload as T
}

function getErrorMessage(payload: unknown): string {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'detail' in payload &&
    typeof payload.detail === 'string'
  ) {
    return payload.detail
  }

  return 'Не удалось выполнить запрос к API.'
}
