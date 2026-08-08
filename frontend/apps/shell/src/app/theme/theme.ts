import { createTheme } from '@mui/material/styles'

import { semanticColors } from './foundations'

export const theme = createTheme({
  palette: {
    primary: {
      main: semanticColors['color/bg/primary'],
      dark: semanticColors['color/bg/primary-hover'],
      contrastText: semanticColors['color/text/inverse'],
    },
    background: {
      default: semanticColors['color/bg/default'],
      paper: semanticColors['color/bg/surface'],
    },
    text: {
      primary: semanticColors['color/text/primary'],
      secondary: semanticColors['color/text/secondary'],
      disabled: semanticColors['color/text/disabled'],
    },
    action: {
      disabled: semanticColors['color/text/disabled'],
      disabledBackground: semanticColors['color/bg/disabled'],
    },
    divider: semanticColors['color/border/default'],
    success: {
      main: semanticColors['color/state/success'],
    },
    error: {
      main: semanticColors['color/state/error'],
    },
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
  },
  shape: {
    borderRadius: 12,
  },
})
