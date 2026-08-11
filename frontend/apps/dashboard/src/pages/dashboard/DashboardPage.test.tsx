import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { DashboardPage } from './DashboardPage'
import type { SearchProfile } from './model/types'

const createProfile = (
  skills: string[],
  searchActive = true,
): SearchProfile => ({
  specialization: 'Инженер по информационной безопасности',
  skills,
  workFormat: 'Удалённо',
  salary: 'от 150 000 ₽',
  level: 'Junior+',
  searchActive,
})

const renderDashboard = (
  skills: string[],
  onEdit = vi.fn(),
  onStatisticsClick = vi.fn(),
  searchActive = true,
) =>
  render(
    <DashboardPage
      profile={createProfile(skills, searchActive)}
      onEdit={onEdit}
      onStatisticsClick={onStatisticsClick}
    />,
  )

describe('DashboardPage', () => {
  it('renders the approved dashboard content and long specialization', () => {
    renderDashboard(['React', 'TypeScript'])

    expect(
      screen.getByRole('heading', {
        name: 'Инженер по информационной безопасности',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Поиск активен')
    expect(
      screen.getByRole('heading', { name: 'Новые вакансии' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Пока новых вакансий нет')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Открыть статистику' }),
    ).toBeInTheDocument()
  })

  it('shows two read-only shared chips without an overflow indicator', () => {
    renderDashboard(['React', 'TypeScript'])

    const skills = screen.getByLabelText('Навыки')
    expect(within(skills).getByText('React')).toBeInTheDocument()
    expect(within(skills).getByText('TypeScript')).toBeInTheDocument()
    expect(within(skills).queryByLabelText(/Ещё \d+ навыков/)).toBeNull()

    const reactChip = within(skills).getByText('React').closest('.MuiChip-root')
    expect(reactChip).not.toHaveAttribute('role', 'button')
    expect(reactChip).not.toHaveAttribute('aria-pressed')
  })

  it('shows the first three of twelve skills and the correct +9 summary', () => {
    const skills = [
      'React',
      'TypeScript',
      'Redux Toolkit',
      'JavaScript',
      'Next.js',
      'HTML',
      'CSS',
      'Sass',
      'Docker',
      'Git',
      'Webpack',
      'Vite',
    ]

    renderDashboard(skills)

    const skillsGroup = screen.getByLabelText('Навыки')
    skills.slice(0, 3).forEach((skill) => {
      expect(within(skillsGroup).getByText(skill)).toBeInTheDocument()
    })
    expect(
      within(skillsGroup).getByLabelText('Ещё 9 навыков'),
    ).toHaveTextContent('+9')
    skills.slice(3).forEach((skill) => {
      expect(within(skillsGroup).queryByText(skill)).toBeNull()
    })
  })

  it('emits edit and statistics intents through callbacks', async () => {
    const user = userEvent.setup()
    const onEdit = vi.fn()
    const onStatisticsClick = vi.fn()
    renderDashboard([], onEdit, onStatisticsClick)

    await user.click(screen.getByRole('button', { name: /Изменить/ }))
    await user.click(
      screen.getByRole('button', { name: 'Открыть статистику' }),
    )

    expect(onEdit).toHaveBeenCalledOnce()
    expect(onStatisticsClick).toHaveBeenCalledOnce()
  })

  it('renders search status only for an active profile', () => {
    const { rerender } = renderDashboard([], vi.fn(), vi.fn(), false)

    expect(screen.queryByRole('status')).toBeNull()

    rerender(
      <DashboardPage
        profile={createProfile([], true)}
        onEdit={vi.fn()}
        onStatisticsClick={vi.fn()}
      />,
    )
    expect(screen.getByRole('status')).toHaveTextContent('Поиск активен')
  })
})
