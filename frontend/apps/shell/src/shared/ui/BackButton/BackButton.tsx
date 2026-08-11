import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import MuiButton, {
  buttonClasses,
} from "@mui/material/Button";
import { styled } from "@mui/material/styles";
import { forwardRef } from "react";

import { semanticColors } from "@jobmonitor/ui";
import type { BackButtonProps } from "./BackButton.types";

const NavigationButton = styled(MuiButton)({
  width: "fit-content",
  minWidth: 0,
  height: 44,

  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 4,

  borderRadius: 8,
  paddingInline: 8,

  backgroundColor: "transparent",
  color: semanticColors["color/text/brand"],

  fontSize: 14,
  fontWeight: 500,
  lineHeight: "20px",
  textTransform: "none",

  "&:hover": {
    backgroundColor: semanticColors["color/bg/primary-subtle"],
  },

  [`&.${buttonClasses.focusVisible}`]: {
    outline: `2px solid ${semanticColors["color/border/brand"]}`,
    outlineOffset: 2,
  },

  [`&.${buttonClasses.disabled}`]: {
    color: semanticColors["color/text/disabled"],
  },

  [`&.${buttonClasses.disabled} .MuiSvgIcon-root`]: {
    color: semanticColors["color/text/disabled"],
  },
});

export const BackButton = forwardRef<HTMLButtonElement, BackButtonProps>(
  ({ label = "Назад", ...props }, ref) => {
    return (
      <NavigationButton ref={ref} variant="text" {...props}>
        <ChevronLeftIcon
          sx={{
            fontSize: 18,
            color: semanticColors["color/icon/brand"],
            display: "block",
            flexShrink: 0,
          }}
        />
        {label}
      </NavigationButton>
    );
  },
);

BackButton.displayName = "BackButton";
