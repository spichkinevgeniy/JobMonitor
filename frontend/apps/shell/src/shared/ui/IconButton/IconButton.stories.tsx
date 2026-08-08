import CloseIcon from '@mui/icons-material/Close'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'

import { IconButton } from './IconButton'

const meta = {
  title: 'Shared/IconButton',
  component: IconButton,
  args: {
    onClick: fn(),
  },
} satisfies Meta<typeof IconButton>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  name: 'Default / Menu',
  args: {
    'aria-label': 'Открыть меню',
    children: <MoreVertIcon />,
  },
}

export const Close: Story = {
  args: {
    'aria-label': 'Закрыть',
    children: <CloseIcon />,
  },
}

export const Disabled: Story = {
  args: {
    'aria-label': 'Открыть меню',
    children: <MoreVertIcon />,
    disabled: true,
  },
}
