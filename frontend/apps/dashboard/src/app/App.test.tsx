import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { initializeTelegramWebAppMock, queryMock } = vi.hoisted(() => ({
  initializeTelegramWebAppMock: vi.fn(),
  queryMock: vi.fn(),
}))

vi.mock('@jobmonitor/telegram', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@jobmonitor/telegram')>()
  return {
    ...actual,
    initializeTelegramWebApp: initializeTelegramWebAppMock,
  }
})

vi.mock('../pages/dashboard/api', async (importOriginal) => {
  const actual = await importOriginal<
    typeof import('../pages/dashboard/api')
  >()
  return {
    ...actual,
    useGetSearchProfileQuery: queryMock,
  }
})

import App from './App'

const apiProfile = {
  specializations: ['Frontend'],
  skills: ['React', 'TypeScript'],
  work_formats: ['REMOTE'],
  salary: { mode: 'FROM', amount_rub: 150000 },
  level: { grade: 'JUNIOR', mode: 'AT_LEAST' },
  search_active: true,
}

beforeEach(() => {
  queryMock.mockReset()
  initializeTelegramWebAppMock.mockReset()
})

describe('App search profile boundary', () => {
  it('shows loading without rendering a fake profile', () => {
    queryMock.mockReturnValue({
      data: undefined,
      error: undefined,
      isError: false,
      isLoading: true,
      refetch: vi.fn(),
    })

    render(<App />)

    expect(screen.getByText('Загружаем профиль')).toBeInTheDocument()
    expect(screen.queryByText('Frontend')).toBeNull()
    expect(initializeTelegramWebAppMock).toHaveBeenCalledOnce()
  })

  it('shows the API error and retries without falling back to mock data', async () => {
    const user = userEvent.setup()
    const refetch = vi.fn()
    queryMock.mockReturnValue({
      data: undefined,
      error: { data: { detail: 'Профиль поиска ещё не завершён.' } },
      isError: true,
      isLoading: false,
      refetch,
    })

    render(<App />)

    expect(screen.getByText('Профиль поиска ещё не завершён.')).toBeInTheDocument()
    expect(screen.queryByText('Frontend')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Повторить' }))
    expect(refetch).toHaveBeenCalledOnce()
  })

  it('maps the API response before rendering DashboardPage', () => {
    queryMock.mockReturnValue({
      data: apiProfile,
      error: undefined,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    })

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Frontend' })).toBeInTheDocument()
    expect(screen.getByText('Удалённо · Junior+ · от 150 000 ₽')).toBeInTheDocument()
  })
})
