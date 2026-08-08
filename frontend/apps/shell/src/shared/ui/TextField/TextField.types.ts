import type { InputBaseProps } from '@mui/material/InputBase'
import type { InputHTMLAttributes, ReactNode } from 'react'

export interface TextFieldProps extends Omit<
  InputBaseProps,
  | 'color'
  | 'endAdornment'
  | 'fullWidth'
  | 'inputRef'
  | 'margin'
  | 'maxRows'
  | 'minRows'
  | 'multiline'
  | 'rows'
  | 'size'
  | 'slotProps'
  | 'startAdornment'
> {
  label?: ReactNode
  helperText?: ReactNode
  startAdornment?: ReactNode
  endAdornment?: ReactNode
  inputMode?: InputHTMLAttributes<HTMLInputElement>['inputMode']
}
