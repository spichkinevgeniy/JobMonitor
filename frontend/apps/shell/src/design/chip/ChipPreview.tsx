import { Box, Typography } from "@mui/material";
import { Chip, semanticColors } from "@jobmonitor/ui";
import type { ReactNode } from "react";

import {
  DesignPreviewCard,
  DesignPreviewPage,
} from "@/design/shared/DesignPreview";

interface PreviewStateProps {
  label: string;
  children: ReactNode;
  height?: number;
  group?: boolean;
}

const handleChipClick = () => undefined;

const PreviewState = ({
  label,
  children,
  height = 180,
  group = false,
}: PreviewStateProps) => (
  <Box
    sx={{
      boxSizing: "border-box",
      width: "100%",
      height,
      display: "grid",
      gridTemplateRows: "auto 1fr",
      gap: 1,
      p: 2,
      border: `1px solid ${semanticColors["color/border/default"]}`,
      borderRadius: "12px",
      backgroundColor: semanticColors["color/bg/surface"],
    }}
  >
    <Typography
      sx={{
        color: "text.secondary",
        fontSize: 13,
        fontWeight: 600,
      }}
    >
      {label}
    </Typography>

    <Box
      sx={{
        minWidth: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {group ? (
        /*
         * Для кейсов с несколькими компонентами
         * audit-target — вся группа.
         */
        <Box
          data-audit-target
          data-audit-content-mode="none"
          sx={{
            width: "fit-content",
            maxWidth: "100%",
          }}
        >
          {children}
        </Box>
      ) : (
        /*
         * Для одиночного компонента этот wrapper
         * обжимается точно по размеру Chip.
         */
        <Box
          data-audit-target
          sx={{
            display: "inline-flex",
            width: "fit-content",
            height: "fit-content",
          }}
        >
          {children}
        </Box>
      )}
    </Box>
  </Box>
);

const ChipPreview = () => (
  <DesignPreviewPage
    title="Chip"
    description="JobMonitor UI · Selectable skill · 32px"
    canvasWidth={560}
    columns={2}
  >
    <DesignPreviewCard title="Default">
      <PreviewState label="Default">
        <Chip label="JavaScript" selected={false} onClick={handleChipClick} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Selected">
      <PreviewState label="Selected">
        <Chip label="React" selected onClick={handleChipClick} />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Disabled">
      <PreviewState label="Disabled">
        <Chip
          label="Docker"
          selected={false}
          disabled
          onClick={handleChipClick}
        />
      </PreviewState>
    </DesignPreviewCard>

    <DesignPreviewCard title="Skills wrap">
      <PreviewState label="Skills wrap" height={320} group>
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: 1,
          }}
        >
          <Chip label="React" selected onClick={handleChipClick} />
          <Chip label="TypeScript" selected onClick={handleChipClick} />
          <Chip label="JavaScript" selected={false} onClick={handleChipClick} />
          <Chip label="Node.js" selected={false} onClick={handleChipClick} />
          <Chip label="Python" selected={false} onClick={handleChipClick} />
          <Chip label="SQL" selected={false} onClick={handleChipClick} />
          <Chip label="Docker" selected={false} onClick={handleChipClick} />
        </Box>
      </PreviewState>
    </DesignPreviewCard>
  </DesignPreviewPage>
);

export default ChipPreview;
