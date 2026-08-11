import type { BaseQueryApi } from '@reduxjs/toolkit/query'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { TelegramWebApp } from '../web-app'
import { createTelegramBaseQuery } from './createTelegramBaseQuery'

const createApi = (): BaseQueryApi => ({
  signal: new AbortController().signal,
  abort: vi.fn(),
  dispatch: vi.fn(),
  getState: vi.fn(),
  extra: undefined,
  endpoint: 'test',
  type: 'query',
  forced: false,
  queryCacheKey: 'test',
})

const installTelegramWebApp = (initData: string) => {
  const webApp = {
    initData,
  } as TelegramWebApp

  vi.stubGlobal('window', {
    Telegram: { WebApp: webApp },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createTelegramBaseQuery', () => {
  it('returns the existing authorization error without making a request', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const baseQuery = createTelegramBaseQuery({
      baseUrl: 'https://example.test',
    })

    const result = await baseQuery('/onboarding', createApi(), {})

    expect(result).toEqual({
      error: {
        status: 'CUSTOM_ERROR',
        error: 'Откройте Mini App внутри Telegram.',
      },
    })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('attaches initData only as the Telegram authorization header', async () => {
    installTelegramWebApp('query_id=secret')
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const baseQuery = createTelegramBaseQuery({
      baseUrl: 'https://example.test',
    })

    await baseQuery(
      {
        url: '/onboarding',
        method: 'POST',
        body: { step: 1 },
      },
      createApi(),
      {},
    )

    const request = fetchMock.mock.calls[0]?.[0] as Request
    expect(request.headers.get('X-Telegram-Init-Data')).toBe('query_id=secret')
    expect(await request.clone().json()).toEqual({ step: 1 })
    expect(await request.clone().text()).not.toContain('query_id=secret')
  })
})
