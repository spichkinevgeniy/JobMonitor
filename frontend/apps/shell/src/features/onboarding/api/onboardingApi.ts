import { createApi } from '@reduxjs/toolkit/query/react'
import { createTelegramBaseQuery } from '@jobmonitor/telegram'

import type {
  OnboardingDraftRequest,
  OnboardingStateResponse,
  ResumeImportJobCreated,
  ResumeImportJobStatus,
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
    startResumeImport: builder.mutation<ResumeImportJobCreated, File>({
      query: (file) => {
        const body = new FormData()
        body.append('file', file, file.name)

        return {
          url: '/onboarding/resume-prefill',
          method: 'POST',
          body,
        }
      },
    }),
    getResumeImportStatus: builder.query<ResumeImportJobStatus, string>({
      query: (jobId) => `/onboarding/resume-prefill/${jobId}`,
    }),
  }),
})

export const {
  useCompleteOnboardingMutation,
  useGetOnboardingQuery,
  useLazyGetResumeImportStatusQuery,
  useSaveOnboardingDraftMutation,
  useStartResumeImportMutation,
} = onboardingApi
