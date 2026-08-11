import type { FetchBaseQueryArgs } from '@reduxjs/toolkit/query'

export interface CreateTelegramBaseQueryOptions
  extends Omit<FetchBaseQueryArgs, 'prepareHeaders'> {
  missingTelegramErrorMessage?: string
}
