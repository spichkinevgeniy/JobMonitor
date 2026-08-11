import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DashboardPage } from './DashboardPage'

const createProfile = (skills: string[]) => ({
  specialization: 'Frontend',
  skills,
  workFormat: 'Удалённо',
  salary: 'от 150 000 ₽',
  level: 'Junior+',
  searchActive: true,
})

const renderDashboard = (skills: string[]) =>
  render(
    <DashboardPage
      profile={createProfile(skills)}
      onEdit={() => undefined}
      onStatisticsClick={() => undefined}
    />,
  )

describe('DashboardPage skill summary', () => {
  it.each([
    { skills: [], visibleSkills: [] },
    { skills: ['React'], visibleSkills: ['React'] },
    {
      skills: ['React', 'TypeScript'],
      visibleSkills: ['React', 'TypeScript'],
    },
  ])('shows every skill when the profile has $skills.length', ({
    skills,
    visibleSkills,
  }) => {
    renderDashboard(skills)

    visibleSkills.forEach((skill) => {
      expect(screen.getByText(skill)).toBeInTheDocument()
    })
    expect(screen.queryByLabelText(/Ещё \d+ навыков/)).not.toBeInTheDocument()
  })

  it.each([
    {
      skills: ['React', 'TypeScript', 'Redux', 'JavaScript', 'Next.js'],
      hiddenCount: 2,
    },
    {
      skills: [
        'React',
        'TypeScript',
        'JavaScript',
        'Redux Toolkit',
        'Next.js',
        'HTML',
        'CSS',
        'Sass',
        'Docker',
        'Git',
        'Webpack',
        'Vite',
      ],
      hiddenCount: 9,
    },
    {
      skills: [
        'Очень длинное название технологии',
        'Ещё одно очень длинное название',
        'Третье длинное название навыка',
        'Скрытый навык',
      ],
      hiddenCount: 1,
    },
  ])('shows three skills and a +N indicator for overflow', ({
    skills,
    hiddenCount,
  }) => {
    renderDashboard(skills)

    skills.slice(0, 3).forEach((skill) => {
      expect(screen.getByText(skill)).toBeInTheDocument()
    })
    expect(
      screen.getByLabelText(`Ещё ${hiddenCount} навыков`),
    ).toHaveTextContent(`+${hiddenCount}`)
    expect(screen.queryByText(skills[3])).not.toBeInTheDocument()
  })
})
