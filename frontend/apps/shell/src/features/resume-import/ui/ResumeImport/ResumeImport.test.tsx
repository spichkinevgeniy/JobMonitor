import { ThemeProvider } from '@mui/material'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { theme } from '@jobmonitor/ui'
import { describe, expect, it, vi } from 'vitest'

import { MAX_RESUME_FILE_SIZE_BYTES, ResumeImport } from './ResumeImport'

interface RenderResumeImportOptions {
  onFileSelected?: (file: File) => void
  onResumeAnalyze?: (file: File) => void
  isResumeLoading?: boolean
}

const renderResumeImport = ({
  onFileSelected = vi.fn(),
  onResumeAnalyze = vi.fn(),
  isResumeLoading = false,
}: RenderResumeImportOptions = {}) => {
  const view = render(
    <ThemeProvider theme={theme}>
      <ResumeImport
        onFileSelected={onFileSelected}
        onResumeAnalyze={onResumeAnalyze}
        isResumeLoading={isResumeLoading}
      />
    </ThemeProvider>,
  )

  return {
    input: screen.getByLabelText('Выбрать PDF-резюме') as HTMLInputElement,
    onFileSelected,
    onResumeAnalyze,
    rerenderLoading: (loading: boolean) =>
      view.rerender(
        <ThemeProvider theme={theme}>
          <ResumeImport
            onFileSelected={onFileSelected}
            onResumeAnalyze={onResumeAnalyze}
            isResumeLoading={loading}
          />
        </ThemeProvider>,
      ),
  }
}

describe('ResumeImport', () => {
  it('renders the compact PDF upload control and updated copy', () => {
    const { input } = renderResumeImport()

    expect(
      screen.getByRole('heading', { name: 'Загрузите резюме' }),
    ).toBeVisible()
    expect(
      screen.getByText('Мы попробуем автоматически определить параметры поиска.'),
    ).toBeVisible()
    expect(screen.getByText('Загрузить PDF')).toBeVisible()
    expect(screen.getByTestId('CloudUploadIcon')).toBeVisible()
    expect(input).toHaveAttribute('accept', 'application/pdf')
  })

  it('shows the selected PDF filename', async () => {
    const user = userEvent.setup()
    const { input } = renderResumeImport()

    await user.upload(
      input,
      new File(['resume'], 'ivan-resume.pdf', { type: 'application/pdf' }),
    )

    expect(screen.getByText('Выбран файл: ivan-resume.pdf')).toBeVisible()
    expect(screen.queryByText('Загрузить PDF')).toBeNull()
    expect(screen.getByRole('button', { name: 'Выбрать другое' })).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Анализировать резюме' }),
    ).toBeVisible()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('rejects a non-PDF file', async () => {
    const user = userEvent.setup({ applyAccept: false })
    const { input, onFileSelected } = renderResumeImport()

    await user.upload(
      input,
      new File(['resume'], 'ivan-resume.txt', { type: 'text/plain' }),
    )

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Выберите файл в формате PDF.',
    )
    expect(onFileSelected).not.toHaveBeenCalled()
  })

  it('rejects a PDF larger than 15 MB', async () => {
    const user = userEvent.setup()
    const { input, onFileSelected } = renderResumeImport()
    const file = new File(['resume'], 'large-resume.pdf', {
      type: 'application/pdf',
    })
    Object.defineProperty(file, 'size', {
      value: MAX_RESUME_FILE_SIZE_BYTES + 1,
    })

    await user.upload(input, file)

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Размер файла не должен превышать 15 МБ.',
    )
    expect(onFileSelected).not.toHaveBeenCalled()
  })

  it('passes the selected PDF to the callback', async () => {
    const user = userEvent.setup()
    const onFileSelected = vi.fn()
    const { input } = renderResumeImport({ onFileSelected })
    const file = new File(['resume'], 'ivan-resume.pdf', {
      type: 'application/pdf',
    })

    await user.upload(input, file)

    expect(onFileSelected).toHaveBeenCalledOnce()
    expect(onFileSelected).toHaveBeenCalledWith(file)
  })

  it('analyzes only after the explicit action', async () => {
    const user = userEvent.setup()
    const onResumeAnalyze = vi.fn()
    const { input } = renderResumeImport({ onResumeAnalyze })
    const file = new File(['resume'], 'ivan-resume.pdf', {
      type: 'application/pdf',
    })

    await user.upload(input, file)
    expect(onResumeAnalyze).not.toHaveBeenCalled()

    await user.click(
      screen.getByRole('button', { name: 'Анализировать резюме' }),
    )
    expect(onResumeAnalyze).toHaveBeenCalledOnce()
    expect(onResumeAnalyze).toHaveBeenCalledWith(file)
  })

  it('replaces the selected PDF', async () => {
    const user = userEvent.setup()
    const onFileSelected = vi.fn()
    const { input } = renderResumeImport({ onFileSelected })
    const firstFile = new File(['first'], 'first.pdf', {
      type: 'application/pdf',
    })
    const replacement = new File(['second'], 'replacement.pdf', {
      type: 'application/pdf',
    })

    await user.upload(input, firstFile)
    await user.click(screen.getByRole('button', { name: 'Выбрать другое' }))
    await user.upload(input, replacement)

    expect(screen.getByText('Выбран файл: replacement.pdf')).toBeVisible()
    expect(onFileSelected).toHaveBeenLastCalledWith(replacement)
  })

  it('disables replacement and analysis while loading', async () => {
    const user = userEvent.setup()
    const { input, rerenderLoading } = renderResumeImport()
    const file = new File(['resume'], 'ivan-resume.pdf', {
      type: 'application/pdf',
    })

    await user.upload(input, file)
    rerenderLoading(true)

    expect(input).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Выбрать другое' })).toBeNull()
    expect(
      screen.queryByRole('button', { name: 'Анализировать резюме' }),
    ).toBeNull()
    expect(screen.getByRole('status')).toHaveTextContent('Анализируем резюме...')
    expect(screen.getByRole('progressbar')).toBeVisible()
    expect(screen.getByRole('status')).toHaveTextContent(
      'Это может занять некоторое время.',
    )
    expect(screen.getByRole('status')).toHaveTextContent(
      'Можно закрыть окно — бот сообщит, когда анализ будет готов.',
    )
    expect(screen.queryByText('или заполните вручную')).toBeNull()
  })
})
