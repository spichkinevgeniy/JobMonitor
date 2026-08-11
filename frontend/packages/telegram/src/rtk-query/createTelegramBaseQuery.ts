import {
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from '@reduxjs/toolkit/query'

import { getTelegramInitData } from '../web-app'
import type { CreateTelegramBaseQueryOptions } from './createTelegramBaseQuery.types'

const DEFAULT_MISSING_TELEGRAM_ERROR = 'Откройте Mini App внутри Telegram.'

export const createTelegramBaseQuery = ({
  missingTelegramErrorMessage = DEFAULT_MISSING_TELEGRAM_ERROR,
  ...baseQueryOptions
}: CreateTelegramBaseQueryOptions): BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> => {
  const rawBaseQuery = fetchBaseQuery({
    ...baseQueryOptions,
    prepareHeaders: (headers) => {
      const initData = getTelegramInitData()

      if (initData) {
        headers.set('X-Telegram-Init-Data', initData)
      }

      return headers
    },
  })

  return async (args, api, extraOptions) => {
    if (!getTelegramInitData()) {
      return {
        error: {
          status: 'CUSTOM_ERROR',
          error: missingTelegramErrorMessage,
        },
      }
    }

    return rawBaseQuery(args, api, extraOptions)
  }
}
