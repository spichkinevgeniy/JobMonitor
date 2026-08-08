import type { ChipProps as MuiChipProps } from '@mui/material/Chip'

export interface ChipProps extends Omit<
  MuiChipProps,
  | 'avatar'
  | 'children'
  | 'clickable'
  | 'color'
  | 'deleteIcon'
  | 'icon'
  | 'label'
  | 'onDelete'
  | 'size'
  | 'variant'
> {
  label: string
  selected: boolean
}
