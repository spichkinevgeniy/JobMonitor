import type { IconButtonProps as MuiIconButtonProps } from '@mui/material/IconButton'

export type IconButtonProps = Omit<
  MuiIconButtonProps,
  'color' | 'loading' | 'loadingIndicator' | 'size'
>
