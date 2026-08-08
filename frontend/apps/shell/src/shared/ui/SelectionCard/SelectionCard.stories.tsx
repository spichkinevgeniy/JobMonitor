import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined'
import CodeIcon from '@mui/icons-material/Code'
import StorageIcon from '@mui/icons-material/Storage'
import { Box } from '@mui/material'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState, type MouseEventHandler } from 'react'
import { fn } from 'storybook/test'

import { SelectionCard } from './SelectionCard'

const meta = {
  title: 'Shared/SelectionCard',
  component: SelectionCard,
  args: {
    icon: <CodeIcon />,
    title: 'Frontend',
    description: 'Вёрстка и работа с интерфейсами',
    onClick: fn(),
    selected: false,
  },
  decorators: [
    (Story) => (
      <Box sx={{ width: 328 }}>
        <Story />
      </Box>
    ),
  ],
} satisfies Meta<typeof SelectionCard>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const Selected: Story = {
  args: {
    icon: <StorageIcon />,
    title: 'Backend',
    description: 'Серверная часть и API',
    selected: true,
  },
}

export const Disabled: Story = {
  args: {
    icon: <BugReportOutlinedIcon />,
    title: 'QA',
    description: 'Тестирование и контроль качества',
    disabled: true,
  },
}

interface InteractiveExampleProps {
  onClick?: MouseEventHandler<HTMLButtonElement>
}

const InteractiveExample = ({ onClick }: InteractiveExampleProps) => {
  const [selected, setSelected] = useState(false)

  const handleClick: MouseEventHandler<HTMLButtonElement> = (event) => {
    setSelected((currentSelected) => !currentSelected)
    onClick?.(event)
  }

  return (
    <SelectionCard
      icon={<CodeIcon />}
      title="Frontend"
      description="Вёрстка и работа с интерфейсами"
      selected={selected}
      onClick={handleClick}
    />
  )
}

export const Interactive: Story = {
  render: ({ onClick }) => <InteractiveExample onClick={onClick} />,
}
