import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState, type MouseEventHandler } from 'react'
import { fn } from 'storybook/test'

import { Chip } from './Chip'

const meta = {
  title: 'Shared/Chip',
  component: Chip,
  args: {
    label: 'JavaScript',
    onClick: fn(),
    selected: false,
  },
} satisfies Meta<typeof Chip>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const Selected: Story = {
  args: {
    label: 'React',
    selected: true,
  },
}

export const Disabled: Story = {
  args: {
    label: 'Docker',
    disabled: true,
  },
}

interface InteractiveExampleProps {
  onClick?: MouseEventHandler<HTMLDivElement>
}

const InteractiveExample = ({ onClick }: InteractiveExampleProps) => {
  const [selected, setSelected] = useState(false)

  const handleClick: MouseEventHandler<HTMLDivElement> = (event) => {
    setSelected((currentSelected) => !currentSelected)
    onClick?.(event)
  }

  return (
    <Chip
      label="TypeScript"
      selected={selected}
      onClick={handleClick}
    />
  )
}

export const Interactive: Story = {
  render: ({ onClick }) => <InteractiveExample onClick={onClick} />,
}
