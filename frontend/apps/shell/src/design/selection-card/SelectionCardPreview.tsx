import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined'
import CodeIcon from '@mui/icons-material/Code'
import StorageIcon from '@mui/icons-material/Storage'
import { Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { SelectionCard } from '@/shared/ui/SelectionCard'

interface PreviewStateProps {
  label: string
  children: ReactNode
}

const PreviewState = ({ label, children }: PreviewStateProps) => (
  <Stack spacing={1} sx={{ width: '100%' }}>
    <Typography sx={{ color: 'text.secondary', fontSize: 12, fontWeight: 500 }}>
      {label}
    </Typography>
    {children}
  </Stack>
)

const SelectionCardPreview = () => (
  <DesignPreviewPage
    title="SelectionCard"
    description="JobMonitor UI · Selection control · specialty example"
    canvasWidth={820}
    columns={2}
  >
    <DesignPreviewCard title="Default">
      <PreviewState label="Default">
        <SelectionCard
          icon={<CodeIcon />}
          title="Frontend"
          description="Вёрстка и работа с интерфейсами"
          selected={false}
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Selected">
      <PreviewState label="Selected">
        <SelectionCard
          icon={<StorageIcon />}
          title="Backend"
          description="Серверная часть и API"
          selected
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Disabled">
      <PreviewState label="Disabled">
        <SelectionCard
          icon={<BugReportOutlinedIcon />}
          title="QA"
          description="Тестирование и контроль качества"
          selected={false}
          disabled
        />
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
)

export default SelectionCardPreview
