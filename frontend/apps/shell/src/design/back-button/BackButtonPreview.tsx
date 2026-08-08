import { DesignPreviewCard, DesignPreviewPage } from '@/design/shared/DesignPreview'
import { BackButton } from '@/shared/ui/BackButton'

const BackButtonPreview = () => {
  return (
    <DesignPreviewPage
      title="BackButton"
      description="JobMonitor UI · Navigation control · 44px"
    >
      <DesignPreviewCard title="Default">
        <BackButton />
      </DesignPreviewCard>
    </DesignPreviewPage>
  )
}

export default BackButtonPreview
