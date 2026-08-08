import SearchIcon from '@mui/icons-material/Search'
import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { TextField } from './TextField'

const meta = {
  title: 'Shared/TextField',
  component: TextField,
  args: {
    onChange: fn(),
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 328 }}>
        <Story />
      </Box>
    ),
  ],
} satisfies Meta<typeof TextField>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Введите значение',
  },
}

export const Search: Story = {
  args: {
    placeholder: 'Найдите навык',
    startAdornment: <SearchIcon />,
  },
}

export const Salary: Story = {
  args: {
    label: 'Сумма в месяц, ₽',
    defaultValue: '150 000',
    endAdornment: '₽',
    helperText: 'Укажите сумму до вычета налогов',
  },
}

export const Error: Story = {
  args: {
    label: 'Сумма в месяц, ₽',
    defaultValue: '0',
    error: true,
    helperText: 'Укажите корректную сумму',
  },
}

export const Disabled: Story = {
  args: {
    placeholder: 'Введите значение',
    disabled: true,
  },
}
