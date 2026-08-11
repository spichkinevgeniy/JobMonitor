import { createApi } from '@reduxjs/toolkit/query/react'
import { createTelegramBaseQuery } from '@jobmonitor/telegram'

import type {
  OnboardingDraftRequest,
  OnboardingStateResponse,
} from './types'

const telegramBaseQuery = createTelegramBaseQuery({
  baseUrl: '/miniapp/api',
})

export const onboardingApi = createApi({
  reducerPath: 'onboardingApi',
  baseQuery: telegramBaseQuery,
  tagTypes: ['Onboarding'],
  endpoints: (builder) => ({
    getOnboarding: builder.query<OnboardingStateResponse, void>({
      query: () => '/onboarding',
      providesTags: ['Onboarding'],
    }),
    saveOnboardingDraft: builder.mutation<
      OnboardingStateResponse,
      OnboardingDraftRequest
    >({
      query: (body) => ({
        url: '/onboarding/draft',
        method: 'PATCH',
        body,
      }),
      async onQueryStarted(_request, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled
          dispatch(
            onboardingApi.util.upsertQueryData('getOnboarding', undefined, data),
          )
        } catch {
          // The mutation hook exposes the request error to the page.
        }
      },
    }),
    completeOnboarding: builder.mutation<OnboardingStateResponse, void>({
      query: () => ({
        url: '/onboarding/complete',
        method: 'POST',
      }),
      async onQueryStarted(_request, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled
          dispatch(
            onboardingApi.util.upsertQueryData('getOnboarding', undefined, data),
          )
        } catch {
          // The mutation hook exposes the request error to the page.
        }
      },
    }),
  }),
})

export const {
  useCompleteOnboardingMutation,
  useGetOnboardingQuery,
  useSaveOnboardingDraftMutation,
} = onboardingApi
