import type { ButtonProps as MuiButtonProps } from '@mui/material/Button'

export type BackButtonProps = Omit<
  MuiButtonProps,
  | 'children'
  | 'color'
  | 'endIcon'
  | 'fullWidth'
  | 'loading'
  | 'loadingIndicator'
  | 'loadingPosition'
  | 'size'
  | 'startIcon'
  | 'variant'
>
