import { createApi } from '@reduxjs/toolkit/query/react'
import { createTelegramBaseQuery } from '@jobmonitor/telegram'

import type { SearchProfileResponse } from './types'

const telegramBaseQuery = createTelegramBaseQuery({
  baseUrl: '/miniapp/api',
})

export const dashboardApi = createApi({
  reducerPath: 'dashboardApi',
  baseQuery: telegramBaseQuery,
  endpoints: (builder) => ({
    getSearchProfile: builder.query<SearchProfileResponse, void>({
      query: () => '/search-profile',
    }),
  }),
})

export const { useGetSearchProfileQuery } = dashboardApi
