import type { ButtonProps as MuiButtonProps } from '@mui/material/Button'

export type ButtonProps = Omit<
  MuiButtonProps,
  | 'color'
  | 'disableElevation'
  | 'loadingIndicator'
  | 'loadingPosition'
  | 'variant'
>
