import { useEffect } from 'react'

import { initializeTelegramWebApp } from '@/shared/lib/telegram'

const App = () => {
  useEffect(() => {
    initializeTelegramWebApp()
  }, [])

  return <main>JobMonitor</main>
}

export default App
