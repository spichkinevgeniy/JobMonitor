import { configureStore } from '@reduxjs/toolkit'

import { onboardingApi } from '@/features/onboarding/api'

export const createAppStore = () =>
  configureStore({
    reducer: {
      [onboardingApi.reducerPath]: onboardingApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(onboardingApi.middleware),
  })

export const store = createAppStore()

export type AppStore = ReturnType<typeof createAppStore>
export type RootState = ReturnType<AppStore['getState']>
export type AppDispatch = AppStore['dispatch']
