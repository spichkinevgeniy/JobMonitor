import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import React from 'react'

import { Button } from './Button'

const meta = {
  title: 'Shared/Button',
  component: Button,
  args: {
    children: 'Продолжить',
  },
} satisfies Meta<typeof Button>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    fullWidth: true,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 328 }}>
        <Story />
      </Box>
    ),
  ],
}

export const Disabled: Story = {
  args: {
    disabled: true,
    fullWidth: true,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 328 }}>
        <Story />
      </Box>
    ),
  ],
}

export const Loading: Story = {
  args: {
    fullWidth: true,
    loading: true,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 328 }}>
        <Story />
      </Box>
    ),
  ],
}

export const HugWidth: Story = {
  args: {
    fullWidth: false,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 'fit-content' }}>
        <Story />
      </Box>
    ),
  ],
}
