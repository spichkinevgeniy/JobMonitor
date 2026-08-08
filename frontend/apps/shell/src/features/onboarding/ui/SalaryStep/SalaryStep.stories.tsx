import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { SalaryStep } from './SalaryStep'

const meta = {
  title: 'Features/Onboarding/SalaryStep',
  component: SalaryStep,
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
} satisfies Meta<typeof SalaryStep>

export default meta

type Story = StoryObj<typeof meta>

export const AnySalary: Story = {
  args: {
    initialValue: {
      mode: 'any',
      amount: null,
    },
  },
}

export const FromSalary: Story = {
  args: {
    initialValue: {
      mode: 'from',
      amount: 150000,
    },
  },
}
