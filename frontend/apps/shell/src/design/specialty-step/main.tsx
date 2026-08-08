import { CssBaseline, ThemeProvider } from '@mui/material'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { theme } from '@/app/theme/theme'
import SpecialtyStepPreview from './SpecialtyStepPreview'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SpecialtyStepPreview />
    </ThemeProvider>
  </StrictMode>,
)
