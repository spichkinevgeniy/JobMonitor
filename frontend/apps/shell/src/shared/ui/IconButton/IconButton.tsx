import MuiIconButton, {
  iconButtonClasses,
} from "@mui/material/IconButton";
import { styled } from "@mui/material/styles";
import { forwardRef } from "react";

import { semanticColors } from "@jobmonitor/ui";
import type { IconButtonProps } from "./IconButton.types";

const JobMonitorIconButton = styled(MuiIconButton)({
  width: 44,
  height: 44,
  border: 0,
  borderRadius: 8,
  backgroundColor: "transparent",
  color: semanticColors["color/icon/secondary"],
  boxShadow: "none",
  "&:hover": {
    backgroundColor: semanticColors["color/bg/subtle"],
  },
  "&.Mui-focusVisible": {
    outline: `2px solid ${semanticColors["color/border/brand"]}`,
    outlineOffset: 2,
  },
  [`&.${iconButtonClasses.disabled}`]: {
    backgroundColor: "transparent",
    color: semanticColors["color/icon/disabled"],
  },
  "& .MuiSvgIcon-root": {
    fontSize: 20,
  },
});

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (props, ref) => <JobMonitorIconButton ref={ref} {...props} />,
);

IconButton.displayName = "IconButton";
