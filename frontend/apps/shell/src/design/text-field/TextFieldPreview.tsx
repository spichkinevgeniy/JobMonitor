import SearchIcon from '@mui/icons-material/Search'
import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { semanticColors } from '@jobmonitor/ui'
import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { TextField } from '@/shared/ui/TextField'

interface PreviewStateProps {
  label: string
  children: ReactNode
}

const auditInputProps = {
  'data-audit-typography': true,
}

const PreviewState = ({ label, children }: PreviewStateProps) => (
  <Box
    sx={{
      boxSizing: 'border-box',
      width: '100%',
      height: 184,
      display: 'grid',
      gridTemplateRows: 'auto 1fr',
      gap: 1,
      p: 2,
      border: `1px solid ${semanticColors['color/border/default']}`,
      borderRadius: '12px',
      backgroundColor: semanticColors['color/bg/surface'],
    }}
  >
    <Typography sx={{ color: 'text.secondary', fontSize: 13, fontWeight: 600 }}>
      {label}
    </Typography>
    <Box
      sx={{
        minWidth: 0,
        display: 'flex',
        alignItems: 'center',
      }}
    >
      {children}
    </Box>
  </Box>
)

const TextFieldPreview = () => (
  <DesignPreviewPage
    title="TextField"
    description="JobMonitor UI · Universal input · 48px"
    canvasWidth={640}
    columns={2}
  >
    <DesignPreviewCard title="Default">
      <PreviewState label="Default">
        <TextField
          data-audit-target
          data-audit-root
          inputProps={auditInputProps}
          placeholder="Введите значение"
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Search">
      <PreviewState label="Search">
        <TextField
          data-audit-target
          data-audit-root
          inputProps={auditInputProps}
          placeholder="Найдите навык"
          startAdornment={<SearchIcon />}
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Salary">
      <PreviewState label="Salary">
        <TextField
          data-audit-target
          data-audit-root
          inputProps={auditInputProps}
          label="Сумма в месяц, ₽"
          defaultValue="150 000"
          endAdornment="₽"
          helperText="Укажите сумму до вычета налогов"
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Error">
      <PreviewState label="Error">
        <TextField
          data-audit-target
          data-audit-root
          inputProps={auditInputProps}
          label="Сумма в месяц, ₽"
          defaultValue="0"
          error
          helperText="Укажите корректную сумму"
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Disabled">
      <PreviewState label="Disabled">
        <TextField
          data-audit-target
          data-audit-root
          inputProps={auditInputProps}
          placeholder="Введите значение"
          disabled
        />
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
)

export default TextFieldPreview
