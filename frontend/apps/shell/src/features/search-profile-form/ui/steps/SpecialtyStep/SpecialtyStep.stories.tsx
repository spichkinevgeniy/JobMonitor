import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { SpecialtyStep } from './SpecialtyStep'

const meta = {
  title: 'Features/SearchProfileForm/SpecialtyStep',
  component: SpecialtyStep,
  args: {
    onBack: fn(),
    onContinue: fn(),
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
} satisfies Meta<typeof SpecialtyStep>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const Filled: Story = {
  args: {
    initialValue: {
      specialty: 'Frontend',
      skills: ['React', 'TypeScript'],
    },
  },
}
