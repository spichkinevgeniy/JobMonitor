import { ThemeProvider } from '@mui/material'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createAppStore } from '@/app/store'
import { SearchProfileForm } from '@/features/search-profile-form'
import { theme } from '@jobmonitor/ui'

const emptyDraft = {
  specializations: [],
  specialty: null,
  skills: [],
  work_formats: null,
  salary: null,
  level: null,
}

const prefilledDraft = {
  specializations: ['Frontend', 'Backend'],
  specialty: 'Frontend',
  skills: ['React', 'TypeScript', 'Node.js'],
  work_formats: ['REMOTE', 'HYBRID'],
  salary: { mode: 'FROM', amount_rub: 180000 },
  level: 'MIDDLE',
}

const state = (
  currentStep: 'SPECIALTY' | 'WORK_FORMAT' | 'SALARY' | 'LEVEL' = 'SPECIALTY',
  draft: Record<string, unknown> = emptyDraft,
) => ({
  completed: false,
  completed_at: null,
  current_step: currentStep,
  max_visited_step: currentStep,
  draft,
})

const response = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )

const requestPath = (input: RequestInfo | URL) =>
  new URL((input as Request).url).pathname

const renderForm = () =>
  render(
    <Provider store={createAppStore()}>
      <ThemeProvider theme={theme}>
        <SearchProfileForm />
      </ThemeProvider>
    </Provider>,
  )

const selectAndAnalyze = () => {
  const file = new File(['resume-content'], 'resume.pdf', {
    type: 'application/pdf',
  })
  fireEvent.change(screen.getByLabelText('Выбрать PDF-резюме'), {
    target: { files: [file] },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Анализировать резюме' }),
  )
  return file
}

describe('SearchProfileForm resume API flow', () => {
  beforeEach(() => {
    window.Telegram = {
      WebApp: {
        initData: 'signed-test-init-data',
        initDataUnsafe: {},
        version: '8.0',
        platform: 'test',
        colorScheme: 'light',
        themeParams: {},
        ready: vi.fn(),
        expand: vi.fn(),
        close: vi.fn(),
        isVersionAtLeast: vi.fn(() => true),
      },
    }
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('posts the PDF, polls to completion, refetches, and shows all prefilled steps', async () => {
    let onboardingGets = 0
    let statusGets = 0
    let postRequest: Request | null = null
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const request = input as Request
      const path = requestPath(input)

      if (path === '/miniapp/api/onboarding' && request.method === 'GET') {
        onboardingGets += 1
        return response(
          onboardingGets === 1 ? state() : state('SPECIALTY', prefilledDraft),
        )
      }
      if (
        path === '/miniapp/api/onboarding/resume-prefill' &&
        request.method === 'POST'
      ) {
        postRequest = request
        return response({ job_id: 'job-1', status: 'queued' })
      }
      if (path === '/miniapp/api/onboarding/resume-prefill/job-1') {
        statusGets += 1
        return response({
          job_id: 'job-1',
          status: statusGets === 1 ? 'processing' : 'completed',
          error: null,
        })
      }
      if (path === '/miniapp/api/onboarding/draft') {
        const nextStep =
          onboardingGets === 2
            ? 'WORK_FORMAT'
            : onboardingGets === 3
              ? 'SALARY'
              : 'LEVEL'
        onboardingGets += 1
        return response(state(nextStep, prefilledDraft))
      }
      throw new Error(`Unexpected request: ${request.method} ${path}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    renderForm()
    await screen.findByText('Загрузите резюме')
    vi.useFakeTimers()

    const file = selectAndAnalyze()
    expect(screen.getByRole('status')).toHaveTextContent('Анализируем резюме...')
    expect(screen.getByRole('progressbar')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Назад' })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Frontend/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Продолжить' })).toBeDisabled()

    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(statusGets).toBe(1)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1750)
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })
    expect(statusGets).toBe(2)
    vi.useRealTimers()

    expect(onboardingGets).toBe(2)
    expect(postRequest).not.toBeNull()
    const multipartRequest = postRequest as unknown as Request
    expect(multipartRequest.headers.get('Content-Type')).toMatch(
      /^multipart\/form-data; boundary=/,
    )
    const multipartBody = await multipartRequest.clone().text()
    expect(multipartBody).toContain('name="file"')
    expect(multipartBody).toContain('Content-Type: application/pdf')
    expect(file.name).toBe('resume.pdf')

    const frontend = screen.getByRole('button', { name: /Frontend/ })
    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Backend/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'React' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(frontend).toBeEnabled()

    fireEvent.click(frontend)
    expect(frontend).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(frontend)
    fireEvent.click(screen.getByRole('button', { name: 'Продолжить' }))
    await screen.findByText('Как хотите работать?')
    expect(screen.getByRole('button', { name: /Удалённо/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: /Гибрид/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    fireEvent.click(screen.getByRole('button', { name: 'Продолжить' }))
    await screen.findByText('Какую зарплату ищете?')
    expect(screen.getByDisplayValue('180 000')).toBeVisible()

    fireEvent.click(screen.getByRole('button', { name: 'Продолжить' }))
    await screen.findByText('Какой у вас уровень?')
    expect(screen.getByRole('button', { name: 'Middle' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('restores the editable form and reports a failed job without further polling', async () => {
    let statusGets = 0
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const request = input as Request
        const path = requestPath(input)
        if (path === '/miniapp/api/onboarding' && request.method === 'GET') {
          return response(state())
        }
        if (path === '/miniapp/api/onboarding/resume-prefill') {
          return response({ job_id: 'job-failed', status: 'queued' })
        }
        statusGets += 1
        return response({
          job_id: 'job-failed',
          status: 'failed',
          error: 'Резюме не удалось распознать.',
        })
      }),
    )
    renderForm()
    const frontend = await screen.findByRole('button', { name: /Frontend/ })
    fireEvent.click(frontend)
    selectAndAnalyze()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Резюме не удалось распознать.',
    )
    expect(frontend).toBeEnabled()
    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Назад' })).toBeEnabled()
    expect(
      screen.getByRole('button', { name: 'Анализировать резюме' }),
    ).toBeEnabled()
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(statusGets).toBe(1)
  })

  it('restores the editable form when the initial request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const request = input as Request
        const path = requestPath(input)
        return path === '/miniapp/api/onboarding' && request.method === 'GET'
          ? response(state())
          : response({ detail: 'Сервис анализа временно недоступен.' }, 503)
      }),
    )
    renderForm()
    await screen.findByText('Загрузите резюме')
    selectAndAnalyze()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Сервис анализа временно недоступен.',
    )
    expect(screen.getByRole('button', { name: /Frontend/ })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Назад' })).toBeEnabled()
    expect(
      screen.getByRole('button', { name: 'Анализировать резюме' }),
    ).toBeEnabled()
  })

  it('stops and restores the form when polling fails', async () => {
    let statusGets = 0
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const request = input as Request
        const path = requestPath(input)
        if (path === '/miniapp/api/onboarding' && request.method === 'GET') {
          return response(state())
        }
        if (path === '/miniapp/api/onboarding/resume-prefill') {
          return response({ job_id: 'job-poll-error', status: 'queued' })
        }
        statusGets += 1
        return response({ detail: 'Не удалось проверить статус анализа.' }, 500)
      }),
    )
    renderForm()
    await screen.findByText('Загрузите резюме')
    selectAndAnalyze()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Не удалось проверить статус анализа.',
    )
    expect(screen.getByRole('button', { name: /Frontend/ })).toBeEnabled()
    await waitFor(() => expect(statusGets).toBe(1))
  })
})
