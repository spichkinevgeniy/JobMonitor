import { initializeTelegramWebApp } from '@jobmonitor/telegram'
import { useEffect } from 'react'

import {
  DashboardPage,
} from '../pages/dashboard'
import {
  getDashboardErrorMessage,
  searchProfileFromApi,
  useGetSearchProfileQuery,
} from '../pages/dashboard/api'
import { DashboardStatusScreen } from '../pages/dashboard/ui/DashboardStatusScreen'

const settingsUrl = '/miniapp/react/?mode=settings'

const handleEdit = () => {
  window.location.assign(settingsUrl)
}

const handleStatisticsClick = () => undefined

const App = () => {
  const searchProfileQuery = useGetSearchProfileQuery()

  useEffect(() => {
    initializeTelegramWebApp()
  }, [])

  if (searchProfileQuery.isError) {
    return (
      <DashboardStatusScreen
        title="Не удалось загрузить профиль"
        description={getDashboardErrorMessage(searchProfileQuery.error)}
        onRetry={() => void searchProfileQuery.refetch()}
      />
    )
  }

  if (searchProfileQuery.isLoading || !searchProfileQuery.data) {
    return (
      <DashboardStatusScreen
        loading
        title="Загружаем профиль"
        description="Получаем актуальные параметры поиска."
      />
    )
  }

  const profile = searchProfileFromApi(searchProfileQuery.data)

  return (
    <DashboardPage
      profile={profile}
      onEdit={handleEdit}
      onStatisticsClick={handleStatisticsClick}
    />
  )
}

export default App
