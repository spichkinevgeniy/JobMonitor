import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Chip } from './Chip'

describe('Chip', () => {
  it('preserves selectable chip semantics and selected indicator', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()

    render(<Chip label="React" selected onClick={onClick} />)

    const chip = screen.getByRole('button', { name: 'React' })
    expect(chip).toHaveAttribute('aria-pressed', 'true')
    expect(chip.querySelector('.JobMonitorChip-check')).toBeInTheDocument()

    await user.click(chip)
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('renders without interactive selection semantics when onClick is absent', () => {
    render(<Chip label="TypeScript" />)

    const chip = screen.getByText('TypeScript').closest('.MuiChip-root')
    expect(chip).toBeInTheDocument()
    expect(chip).not.toHaveAttribute('role', 'button')
    expect(chip).not.toHaveAttribute('aria-pressed')
    expect(chip?.querySelector('.JobMonitorChip-check')).not.toBeInTheDocument()
    expect(chip).not.toHaveClass('MuiChip-clickable')
  })
})
