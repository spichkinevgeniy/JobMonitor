import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { ProgressStepper } from './ProgressStepper'

const meta = {
  title: 'Shared/ProgressStepper',
  component: ProgressStepper,
  args: {
    currentStep: 1,
    totalSteps: 4,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 320 }}>
        <Story />
      </Box>
    ),
  ],
} satisfies Meta<typeof ProgressStepper>

export default meta

type Story = StoryObj<typeof meta>

export const FirstStep: Story = {}

export const SecondStep: Story = {
  args: {
    currentStep: 2,
  },
}

export const ThirdStep: Story = {
  args: {
    currentStep: 3,
  },
}

export const FinalStep: Story = {
  args: {
    currentStep: 4,
  },
}

export const InteractiveCompletedSteps: Story = {
  args: {
    currentStep: 4,
    onStepClick: fn(),
  },
}
