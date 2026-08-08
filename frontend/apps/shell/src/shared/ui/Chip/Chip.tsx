import CheckIcon from "@mui/icons-material/Check";
import MuiChip, {
  chipClasses,
} from "@mui/material/Chip";
import { styled } from "@mui/material/styles";
import { forwardRef } from "react";

import { semanticColors } from "@/app/theme/foundations";
import type { ChipProps } from "./Chip.types";

interface ChipRootProps {
  selected: boolean;
}

const ChipRoot = styled(MuiChip, {
  shouldForwardProp: (prop) => prop !== "selected",
})<ChipRootProps>(({ selected }) => ({
  width: "fit-content",
  height: 32,

  border: `1px solid ${
    selected
      ? semanticColors["color/border/brand"]
      : semanticColors["color/border/default"]
  }`,

  borderRadius: 999,

  backgroundColor: selected
    ? semanticColors["color/bg/primary"]
    : semanticColors["color/bg/surface"],

  color: selected
    ? semanticColors["color/text/inverse"]
    : semanticColors["color/text/primary"],

  fontSize: 14,
  fontWeight: 500,
  lineHeight: "20px",

  boxShadow: "none",

  "&:hover": {
    borderColor: selected
      ? semanticColors["color/border/brand"]
      : semanticColors["color/border/strong"],

    backgroundColor: selected
      ? semanticColors["color/bg/primary"]
      : semanticColors["color/bg/subtle"],
  },

  [`&.${chipClasses.focusVisible}`]: {
    outline: `2px solid ${semanticColors["color/border/brand"]}`,
    outlineOffset: 2,
  },

  [`& .${chipClasses.label}`]: {
    paddingInline: 12,
  },

  "& .JobMonitorChip-content": {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
  },

  "& .JobMonitorChip-check": {
    flexShrink: 0,
    color: semanticColors["color/icon/inverse"],
    fontSize: 16,
  },

  [`&.${chipClasses.disabled}`]: {
    borderColor: semanticColors["color/border/disabled"],
    backgroundColor: semanticColors["color/bg/disabled"],
    color: semanticColors["color/text/disabled"],
    opacity: 1,
  },
}));

export const Chip = forwardRef<HTMLDivElement, ChipProps>(
  ({ label, selected, ...props }, ref) => (
    <ChipRoot
      ref={ref}
      clickable
      selected={selected}
      aria-pressed={selected}
      {...props}
      label={
        <span className="JobMonitorChip-content">
          <span>{label}</span>

          {selected && (
            <CheckIcon className="JobMonitorChip-check" aria-hidden="true" />
          )}
        </span>
      }
    />
  ),
);

Chip.displayName = "Chip";
