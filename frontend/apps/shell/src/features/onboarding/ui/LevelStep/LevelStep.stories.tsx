import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { LevelStep } from './LevelStep'
import type { LevelStepSummary } from './LevelStep.types'

const demoSummary: LevelStepSummary = {
  specialty: 'Frontend',
  skills: [
    'React',
    'TypeScript',
    'JavaScript',
    'Node.js',
    'Python',
    'SQL',
    'Docker',
  ],
  workFormats: ['remote', 'hybrid'],
  salary: {
    mode: 'from',
    amount: 150000,
  },
}

const meta = {
  title: 'Features/Onboarding/LevelStep',
  component: LevelStep,
  args: {
    summary: demoSummary,
    onBack: fn(),
    onComplete: fn(),
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
} satisfies Meta<typeof LevelStep>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    initialValue: {
      level: null,
    },
  },
}

export const Filled: Story = {
  args: {
    initialValue: {
      level: 'JUNIOR',
    },
  },
}
