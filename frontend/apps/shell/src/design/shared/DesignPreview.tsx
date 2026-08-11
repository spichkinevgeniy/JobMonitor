import { Box, Stack, Typography } from "@mui/material";
import { createContext, type ReactNode, useContext } from "react";

interface DesignPreviewPageProps {
  title: string;
  description: string;
  children: ReactNode;
  canvasWidth?: number;
  columns?: 1 | 2;
}

interface DesignPreviewCardProps {
  title: string;
  children: ReactNode;
  auditId?: string;
}

const DesignPreviewContext = createContext<string | null>(null);

const slugify = (value: string) =>
  value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");

export const DesignPreviewPage = ({
  title,
  description,
  children,
  canvasWidth = 440,
  columns = 1,
}: DesignPreviewPageProps) => {
  return (
    <DesignPreviewContext.Provider value={title}>
      <Box
        component="main"
        data-audit-page={slugify(title)}
        sx={{
          minHeight: "100vh",
          bgcolor: "background.default",
          px: 2,
          py: 4,
        }}
      >
        <Box
          sx={{
            boxSizing: "border-box",
            width: canvasWidth,
            maxWidth: "100%",
            mx: "auto",
            p: 3,
          }}
        >
          <Stack spacing={3}>
            <Box>
              <Typography
                component="h1"
                sx={{
                  color: "text.primary",
                  fontSize: 24,
                  fontWeight: 700,
                }}
              >
                {title}
              </Typography>

              <Typography
                sx={{
                  mt: 0.5,
                  color: "text.secondary",
                  fontSize: 14,
                }}
              >
                {description}
              </Typography>
            </Box>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns:
                  columns === 2 ? "repeat(2, minmax(0, 1fr))" : "1fr",
                gap: 2,
              }}
            >
              {children}
            </Box>
          </Stack>
        </Box>
      </Box>
    </DesignPreviewContext.Provider>
  );
};

export const DesignPreviewCard = ({
  title,
  children,
  auditId,
}: DesignPreviewCardProps) => {
  const componentName = useContext(DesignPreviewContext);

  const resolvedAuditId =
    auditId ?? `${slugify(componentName ?? "unknown")}--${slugify(title)}`;

  return (
    <Box
      data-audit-case
      data-audit-id={resolvedAuditId}
      data-audit-component={componentName ?? undefined}
      data-audit-state={title}
      sx={{
        width: 328,
        maxWidth: "100%",
        mx: "auto",
      }}
    >
      <Typography
        sx={{
          mb: 2,
          color: "text.secondary",
          fontSize: 12,
          fontWeight: 500,
        }}
      >
        {title}
      </Typography>

      {/*
        Служебный контейнер.

        Его НЕ фотографируем.
        Playwright будет брать только его первый DOM-child,
        то есть непосредственно Chip / Button / SelectionCard.
      */}
      <Box
        data-audit-target-container
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {children}
      </Box>
    </Box>
  );
};
