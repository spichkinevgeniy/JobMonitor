import { ThemeProvider } from '@mui/material'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createAppStore, type AppStore } from '@/app/store'
import { theme } from '@jobmonitor/ui'
import {
  onboardingApi,
  type OnboardingStateResponse,
} from '@/features/onboarding/api'
import { SettingsPage } from '@/pages/settings'
import { OnboardingPage } from './OnboardingPage'

const emptyDraft: OnboardingStateResponse['draft'] = {
  specializations: [],
  specialty: null,
  skills: [],
  work_formats: null,
  salary: null,
  level: null,
}

const state = (
  overrides: Partial<OnboardingStateResponse> = {},
): OnboardingStateResponse => ({
  completed: false,
  completed_at: null,
  current_step: 'SPECIALTY',
  max_visited_step: 'SPECIALTY',
  draft: emptyDraft,
  ...overrides,
})

const completeDraft: OnboardingStateResponse['draft'] = {
  specializations: ['Frontend', 'Backend'],
  specialty: 'Frontend',
  skills: ['React', 'TypeScript'],
  work_formats: ['REMOTE', 'HYBRID'],
  salary: { mode: 'FROM', amount_rub: 150000 },
  level: 'JUNIOR_PLUS',
}

const response = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )

const setTelegramEnvironment = () => {
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
}

const renderPage = (store: AppStore = createAppStore()) => {
  render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <OnboardingPage />
      </ThemeProvider>
    </Provider>,
  )
  return store
}

const renderSettingsPage = (
  onComplete?: React.ComponentProps<typeof SettingsPage>['onComplete'],
  store: AppStore = createAppStore(),
) => {
  render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <SettingsPage onComplete={onComplete} />
      </ThemeProvider>
    </Provider>,
  )
  return store
}

describe('OnboardingPage server integration', () => {
  beforeEach(() => {
    setTelegramEnvironment()
    window.history.replaceState({}, '', '/miniapp/react/?mode=onboarding')
  })

  it('hydrates the initial draft and current step from GET', async () => {
    const fetchMock = vi.fn((_input: RequestInfo | URL) =>
      response(
        state({
          draft: {
            ...emptyDraft,
            specializations: ['Frontend'],
            specialty: 'Frontend',
            skills: ['React'],
          },
        }),
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    const frontend = await screen.findByRole('button', { name: /Frontend/ })
    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'React' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    const request = fetchMock.mock.calls[0][0] as Request
    expect(request.headers.get('X-Telegram-Init-Data')).toBe(
      'signed-test-init-data',
    )
  })

  it('saves multiple selected specializations in one draft request', async () => {
    const selectedState = state({
      current_step: 'WORK_FORMAT',
      max_visited_step: 'WORK_FORMAT',
      draft: {
        ...emptyDraft,
        specializations: ['Frontend', 'Backend'],
        specialty: 'Backend',
      },
    })
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => response(state()))
      .mockImplementationOnce(() => response(selectedState))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    renderPage()

    const frontend = await screen.findByRole('button', { name: /Frontend/ })
    const backend = screen.getByRole('button', { name: /Backend/ })
    await user.click(frontend)
    await user.click(backend)

    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(backend).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    const request = fetchMock.mock.calls[1][0] as Request
    expect(await request.clone().json()).toEqual({
      step: 'SPECIALTY',
      navigate_to: 'WORK_FORMAT',
      data: {
        specializations: ['Frontend', 'Backend'],
        skills: [],
      },
    })
  })

  it('returns a client authorization error without issuing a malformed request', async () => {
    delete window.Telegram
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    expect(await screen.findByText('Откройте Mini App внутри Telegram.')).toBeTruthy()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('restores a resumed salary step with its amount', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        response(
          state({
            current_step: 'SALARY',
            max_visited_step: 'SALARY',
            draft: completeDraft,
          }),
        ),
      ),
    )

    renderPage()

    expect(await screen.findByText('Какую зарплату ищете?')).toBeTruthy()
    expect(screen.getByDisplayValue('150 000')).toBeTruthy()
  })

  it('restores a resumed level step and selected level', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        response(
          state({
            current_step: 'LEVEL',
            max_visited_step: 'LEVEL',
            draft: completeDraft,
          }),
        ),
      ),
    )

    renderPage()

    expect(await screen.findByText('Какой у вас уровень?')).toBeTruthy()
    expect(
      screen.getByRole('button', { name: 'Junior и выше' }),
    ).toHaveAttribute('aria-pressed', 'true')
  })

  it('navigates back from a restored empty work format without validating it', async () => {
    const restoredWorkFormat = state({
      current_step: 'WORK_FORMAT',
      max_visited_step: 'WORK_FORMAT',
      draft: {
        ...emptyDraft,
        specializations: ['QA'],
        specialty: 'QA',
        skills: ['TypeScript'],
      },
    })
    const navigated = {
      ...restoredWorkFormat,
      current_step: 'SPECIALTY' as const,
    }
    const fetchMock = vi
      .fn((_input: RequestInfo | URL) => response(restoredWorkFormat))
      .mockImplementationOnce(() => response(restoredWorkFormat))
      .mockImplementationOnce(() => response(navigated))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Назад' }))

    expect(await screen.findByText('Кем хотите работать?')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(
      screen.getByRole('button', { name: 'Перейти к шагу 2' }),
    ).toBeTruthy()
    const request = fetchMock.mock.calls[1][0] as Request
    expect(await request.clone().json()).toEqual({
      step: 'WORK_FORMAT',
      navigate_to: 'SPECIALTY',
      data: null,
    })
  })

  it('navigates from restored empty work format through the earlier stepper', async () => {
    const restoredWorkFormat = state({
      current_step: 'WORK_FORMAT',
      max_visited_step: 'WORK_FORMAT',
      draft: {
        ...emptyDraft,
        specializations: ['QA'],
        specialty: 'QA',
        skills: ['TypeScript'],
      },
    })
    const fetchMock = vi
      .fn((_input: RequestInfo | URL) => response(restoredWorkFormat))
      .mockImplementationOnce(() => response(restoredWorkFormat))
      .mockImplementationOnce(() =>
        response({ ...restoredWorkFormat, current_step: 'SPECIALTY' }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(
      await screen.findByRole('button', { name: 'Перейти к шагу 1' }),
    )

    expect(await screen.findByText('Кем хотите работать?')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('navigates back from a restored empty salary without making ANY durable', async () => {
    const restoredSalary = state({
      current_step: 'SALARY',
      max_visited_step: 'SALARY',
      draft: {
        ...emptyDraft,
        specializations: ['Frontend'],
        specialty: 'Frontend',
        work_formats: ['REMOTE'],
      },
    })
    const fetchMock = vi
      .fn((_input: RequestInfo | URL) => response(restoredSalary))
      .mockImplementationOnce(() => response(restoredSalary))
      .mockImplementationOnce(() =>
        response({ ...restoredSalary, current_step: 'WORK_FORMAT' }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Назад' }))

    expect(await screen.findByText('Как хотите работать?')).toBeTruthy()
    const request = fetchMock.mock.calls[1][0] as Request
    expect(await request.clone().json()).toMatchObject({
      step: 'SALARY',
      navigate_to: 'WORK_FORMAT',
      data: null,
    })
  })

  it('navigates back from a restored empty level without requiring a level', async () => {
    const restoredLevel = state({
      current_step: 'LEVEL',
      max_visited_step: 'LEVEL',
      draft: { ...completeDraft, level: null },
    })
    const fetchMock = vi
      .fn((_input: RequestInfo | URL) => response(restoredLevel))
      .mockImplementationOnce(() => response(restoredLevel))
      .mockImplementationOnce(() =>
        response({ ...restoredLevel, current_step: 'SALARY' }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Назад' }))

    expect(await screen.findByText('Какую зарплату ищете?')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('still prevents continuing from an empty work format', async () => {
    const restoredWorkFormat = state({
      current_step: 'WORK_FORMAT',
      max_visited_step: 'WORK_FORMAT',
      draft: {
        ...emptyDraft,
        specializations: ['Frontend'],
        specialty: 'Frontend',
      },
    })
    const fetchMock = vi.fn((_input: RequestInfo | URL) =>
      response(restoredWorkFormat),
    )
    vi.stubGlobal('fetch', fetchMock)
    renderPage()

    expect(
      await screen.findByRole('button', { name: 'Продолжить' }),
    ).toBeDisabled()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('waits for PATCH success before navigating forward', async () => {
    let resolvePatch!: (value: Response) => void
    const pendingPatch = new Promise<Response>((resolve) => {
      resolvePatch = resolve
    })
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() =>
        response(
          state({
            draft: {
              ...emptyDraft,
              specializations: ['Frontend'],
              specialty: 'Frontend',
            },
          }),
        ),
      )
      .mockImplementationOnce(() => pendingPatch)
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Продолжить' }))
    expect(screen.getByText('Кем хотите работать?')).toBeTruthy()

    resolvePatch(
      await response(
        state({
          current_step: 'WORK_FORMAT',
          max_visited_step: 'WORK_FORMAT',
          draft: {
            ...emptyDraft,
            specializations: ['Frontend'],
            specialty: 'Frontend',
            skills: [],
          },
        }),
      ),
    )

    expect(await screen.findByText('Как хотите работать?')).toBeTruthy()
  })

  it('keeps the current step and dirty edits when PATCH fails', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => response(state()))
      .mockImplementationOnce(() => response({ detail: 'temporary failure' }, 500))
      .mockImplementationOnce(() =>
        response(
          state({
            current_step: 'WORK_FORMAT',
            max_visited_step: 'WORK_FORMAT',
            draft: {
              ...emptyDraft,
              specializations: ['Frontend'],
              specialty: 'Frontend',
              skills: ['React'],
            },
          }),
        ),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    const frontend = await screen.findByRole('button', { name: /Frontend/ })
    await user.click(frontend)
    await user.click(screen.getByRole('button', { name: 'React' }))
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('temporary failure')
    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'React' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )

    await user.click(screen.getByRole('button', { name: 'Продолжить' }))
    expect(await screen.findByText('Как хотите работать?')).toBeTruthy()
  })

  it('does not reopen a completed wizard in onboarding mode', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        response(
          state({
            completed: true,
            completed_at: '2026-08-10T10:00:00Z',
            max_visited_step: 'LEVEL',
            draft: completeDraft,
          }),
        ),
      ),
    )

    renderPage()

    expect(await screen.findByText('Настройка завершена')).toBeTruthy()
    expect(screen.queryByText('Кем хотите работать?')).toBeNull()
  })

  it('opens the active profile editor in settings mode', async () => {
    window.history.replaceState({}, '', '/miniapp/react/?mode=settings')
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        response(
          state({
            completed: true,
            completed_at: '2026-08-10T10:00:00Z',
            max_visited_step: 'LEVEL',
            draft: completeDraft,
          }),
        ),
      ),
    )

    renderSettingsPage()

    expect(await screen.findByText('Кем хотите работать?')).toBeTruthy()
    expect(screen.queryByText('Настройка завершена')).toBeNull()
    expect(screen.getByRole('button', { name: /Frontend/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'React' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('notifies settings only after the saved draft is completed', async () => {
    const levelState = state({
      completed: true,
      completed_at: '2026-08-10T10:00:00Z',
      current_step: 'LEVEL',
      max_visited_step: 'LEVEL',
      draft: completeDraft,
    })
    const completedState = {
      ...levelState,
      completed_at: '2026-08-11T10:00:00Z',
    }
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockImplementationOnce(() => response(levelState))
        .mockImplementationOnce(() => response(levelState))
        .mockImplementationOnce(() => response(completedState)),
    )
    const onComplete = vi.fn()
    const user = userEvent.setup()
    renderSettingsPage(onComplete)

    await user.click(await screen.findByRole('button', { name: 'Начать поиск' }))

    await waitFor(() => expect(onComplete).toHaveBeenCalledOnce())
    expect(onComplete.mock.calls[0][0]).toMatchObject({
      specializations: ['Frontend', 'Backend'],
      skills: ['React', 'TypeScript'],
      workFormats: ['remote', 'hybrid'],
      salary: { mode: 'from', amount: 150000 },
      level: 'JUNIOR_PLUS',
    })
  })

  it('completes only after LEVEL save and complete both succeed', async () => {
    const levelState = state({
      current_step: 'LEVEL',
      max_visited_step: 'LEVEL',
      draft: completeDraft,
    })
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => response(levelState))
      .mockImplementationOnce(() => response(levelState))
      .mockImplementationOnce(() =>
        response({
          ...levelState,
          completed: true,
          completed_at: '2026-08-10T10:00:00Z',
        }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Начать поиск' }))

    expect(await screen.findByText('Настройка завершена')).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('keeps completion failure retryable on the level step', async () => {
    const levelState = state({
      current_step: 'LEVEL',
      max_visited_step: 'LEVEL',
      draft: completeDraft,
    })
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => response(levelState))
      .mockImplementationOnce(() => response(levelState))
      .mockImplementationOnce(() => response({ detail: 'complete failed' }, 500))
      .mockImplementationOnce(() => response(levelState))
      .mockImplementationOnce(() =>
        response({ ...levelState, completed: true, completed_at: 'now' }),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Начать поиск' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('complete failed')
    expect(screen.getByText('Какой у вас уровень?')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Начать поиск' })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: 'Начать поиск' }))
    expect(await screen.findByText('Настройка завершена')).toBeTruthy()
  })

  it('does not expose never-visited future steps as navigation buttons', async () => {
    vi.stubGlobal('fetch', vi.fn(() => response(state())))
    renderPage()

    await screen.findByText('Кем хотите работать?')
    expect(
      screen.queryByRole('button', { name: 'Перейти к шагу 2' }),
    ).toBeNull()
  })

  it('does not overwrite dirty local edits after a background refetch', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => response(state()))
      .mockImplementationOnce(() =>
        response(
          state({
            draft: {
              ...emptyDraft,
              specializations: ['Backend'],
              specialty: 'Backend',
            },
          }),
        ),
      )
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    const store = renderPage()

    const frontend = await screen.findByRole('button', { name: /Frontend/ })
    await user.click(frontend)
    await store
      .dispatch(
        onboardingApi.endpoints.getOnboarding.initiate(undefined, {
          forceRefetch: true,
        }),
      )
      .unwrap()

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(frontend).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Backend/ })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })
})
