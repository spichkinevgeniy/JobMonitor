import type { ButtonBaseProps as MuiButtonBaseProps } from '@mui/material/ButtonBase'
import type { ReactNode } from 'react'

export interface SelectionCardProps extends Omit<
  MuiButtonBaseProps,
  'children' | 'title'
> {
  icon: ReactNode
  title: string
  description?: string
  selected: boolean
}
