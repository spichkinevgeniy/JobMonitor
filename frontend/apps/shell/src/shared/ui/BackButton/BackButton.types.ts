import type { ButtonProps as MuiButtonProps } from '@mui/material/Button'
import type { ReactNode } from 'react'

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
> & {
  label?: ReactNode
}
