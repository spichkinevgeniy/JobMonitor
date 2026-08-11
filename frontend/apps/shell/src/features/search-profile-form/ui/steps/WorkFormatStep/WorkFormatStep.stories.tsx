import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { WorkFormatStep } from './WorkFormatStep'

const meta = {
  title: 'Features/SearchProfileForm/WorkFormatStep',
  component: WorkFormatStep,
  args: {
    onBack: fn(),
    onContinue: fn(),
    onNavigateToStep: fn(),
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 390, maxWidth: '100%' }}>
        <Story />
      </Box>
    ),
  ],
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof WorkFormatStep>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const Filled: Story = {
  args: {
    initialValue: {
      workFormats: ['remote', 'hybrid'],
    },
  },
}
