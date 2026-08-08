import MuiButton, {
  buttonClasses,
} from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import { styled } from "@mui/material/styles";
import { forwardRef } from "react";

import { semanticColors } from "@/app/theme/foundations";
import type { ButtonProps } from "./Button.types";

const PrimaryButton = styled(MuiButton)(({ theme }) => ({
  minHeight: 48,
  borderRadius: 12,
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  fontSize: 16,
  fontWeight: 600,
  lineHeight: 1.5,
  paddingInline: 20,
  textTransform: "none",
  boxShadow: "none",
  "&:hover": {
    backgroundColor: theme.palette.primary.dark,
    boxShadow: "none",
  },
  [`&.${buttonClasses.disabled}`]: {
    backgroundColor: theme.palette.action.disabledBackground,
    color: theme.palette.action.disabled,
    cursor: "not-allowed",
    pointerEvents: "auto",
  },
  [`&.${buttonClasses.loading}.${buttonClasses.disabled}`]: {
    backgroundColor: theme.palette.primary.main,
    color: "transparent",
    cursor: "wait",
  },
  [`& .${buttonClasses.loadingIndicator}`]: {
    color: semanticColors["color/icon/inverse"],
  },
}));

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (props, ref) => {
    return (
      <PrimaryButton
        ref={ref}
        color="primary"
        disableElevation
        loadingIndicator={<CircularProgress color="inherit" size={20} />}
        loadingPosition="center"
        variant="contained"
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
