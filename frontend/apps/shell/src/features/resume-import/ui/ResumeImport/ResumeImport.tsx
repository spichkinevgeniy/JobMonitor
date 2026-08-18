import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import { Box, Button, LinearProgress, Typography } from '@mui/material'
import { styled } from '@mui/material/styles'
import { type ChangeEvent, useRef, useState } from 'react'

import type { ResumeImportProps } from './ResumeImport.types'

export const MAX_RESUME_FILE_SIZE_BYTES = 10 * 1024 * 1024

const isPdf = (file: File) =>
  file.type === 'application/pdf' ||
  (file.type === '' && file.name.toLowerCase().endsWith('.pdf'))

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
})

export const ResumeImport = ({
  onFileSelected,
  onResumeAnalyze,
  isResumeLoading = false,
  analysisError = null,
}: ResumeImportProps) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0]
    event.currentTarget.value = ''

    if (!file) {
      return
    }

    if (!isPdf(file)) {
      setSelectedFile(null)
      setError('Выберите файл в формате PDF.')
      return
    }

    if (file.size > MAX_RESUME_FILE_SIZE_BYTES) {
      setSelectedFile(null)
      setError('Размер файла не должен превышать 10 МБ.')
      return
    }

    setSelectedFile(file)
    setError(null)
    onFileSelected?.(file)
  }

  return (
    <Box component="section" aria-labelledby="resume-import-title" sx={{ mt: 3 }}>
      <Typography
        id="resume-import-title"
        component="h2"
        sx={{ fontSize: 16, fontWeight: 600, lineHeight: '24px' }}
      >
        Загрузите резюме
      </Typography>
      <Typography
        sx={{ mt: 1, color: 'text.secondary', fontSize: 14, lineHeight: '20px' }}
      >
        Мы попробуем автоматически определить параметры поиска.
      </Typography>

      <VisuallyHiddenInput
        ref={inputRef}
        type="file"
        accept="application/pdf"
        aria-label="Выбрать PDF-резюме"
        disabled={isResumeLoading}
        onChange={handleChange}
      />

      {!selectedFile && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Button
            type="button"
            variant="contained"
            startIcon={<CloudUploadIcon />}
            sx={{ textTransform: 'none' }}
            onClick={() => inputRef.current?.click()}
          >
            Загрузить PDF
          </Button>
        </Box>
      )}

      {selectedFile && (
        <Box
          sx={{
            mt: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 1.5,
          }}
        >
          <Typography
            title={selectedFile.name}
            sx={{
              maxWidth: '100%',
              color: 'text.secondary',
              fontSize: 13,
              textAlign: 'center',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            Выбран файл: {selectedFile.name}
          </Typography>
          {isResumeLoading ? (
            <Box role="status" aria-live="polite" sx={{ textAlign: 'center' }}>
              <Typography sx={{ fontSize: 15, fontWeight: 600, lineHeight: '22px' }}>
                Анализируем резюме...
              </Typography>
              <LinearProgress sx={{ mt: 1.5, borderRadius: 1 }} />
              <Typography
                sx={{ mt: 1.5, color: 'text.secondary', fontSize: 13, lineHeight: '18px' }}
              >
                Это может занять некоторое время.
                <br />
                Можно закрыть окно — бот сообщит, когда анализ будет готов.
              </Typography>
            </Box>
          ) : (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 1.5,
              }}
            >
              <Button
                type="button"
                variant="outlined"
                sx={{ textTransform: 'none' }}
                onClick={() => inputRef.current?.click()}
              >
                Выбрать другое
              </Button>
              <Button
                type="button"
                variant="contained"
                sx={{ textTransform: 'none' }}
                onClick={() => onResumeAnalyze?.(selectedFile)}
              >
                Анализировать резюме
              </Button>
            </Box>
          )}
        </Box>
      )}
      {error && (
        <Typography
          role="alert"
          sx={{ mt: 1, color: 'error.main', fontSize: 13, lineHeight: '18px' }}
        >
          {error}
        </Typography>
      )}
      {!error && analysisError && (
        <Typography
          role="alert"
          sx={{ mt: 1, color: 'error.main', fontSize: 13, lineHeight: '18px' }}
        >
          {analysisError}
        </Typography>
      )}

      {!isResumeLoading && (
        <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ height: '1px', flex: 1, bgcolor: 'divider' }} />
          <Typography sx={{ color: 'text.secondary', fontSize: 13, flexShrink: 0 }}>
            или заполните вручную
          </Typography>
          <Box sx={{ height: '1px', flex: 1, bgcolor: 'divider' }} />
        </Box>
      )}
    </Box>
  )
}
