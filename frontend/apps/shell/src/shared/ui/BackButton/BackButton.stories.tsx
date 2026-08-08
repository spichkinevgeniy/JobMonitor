import type { Meta, StoryObj } from '@storybook/react-vite'
import React from 'react'
import { fn } from 'storybook/test'

import { BackButton } from './BackButton'

const meta = {
  title: 'Shared/BackButton',
  component: BackButton,
  args: {
    onClick: fn(),
  },
} satisfies Meta<typeof BackButton>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
