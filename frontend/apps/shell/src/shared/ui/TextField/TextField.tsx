import FormControl from "@mui/material/FormControl";
import FormHelperText, {
  formHelperTextClasses,
} from "@mui/material/FormHelperText";
import FormLabel, { formLabelClasses } from "@mui/material/FormLabel";
import InputAdornment from "@mui/material/InputAdornment";
import InputBase, { inputBaseClasses } from "@mui/material/InputBase";
import { styled } from "@mui/material/styles";
import { forwardRef, useId } from "react";

import { semanticColors } from "@jobmonitor/ui";
import type { TextFieldProps } from "./TextField.types";

const FieldControl = styled(FormControl)({
  width: "100%",
});

const FieldLabel = styled(FormLabel)({
  marginBottom: 8,

  color: semanticColors["color/text/primary"],

  fontSize: 14,
  fontWeight: 500,
  lineHeight: "20px",

  [`&.${formLabelClasses.error}`]: {
    color: semanticColors["color/state/error"],
  },

  [`&.${formLabelClasses.disabled}`]: {
    color: semanticColors["color/text/disabled"],
  },
});

const FieldInput = styled(InputBase)({
  boxSizing: "border-box",

  width: "100%",
  height: 48,

  gap: 8,
  paddingInline: 12,

  border: `1px solid ${semanticColors["color/border/default"]}`,
  borderRadius: 8,

  backgroundColor: semanticColors["color/bg/surface"],
  color: semanticColors["color/text/primary"],

  fontSize: 15,
  fontWeight: 400,
  lineHeight: "20px",

  boxShadow: "none",

  "&:hover": {
    borderColor: semanticColors["color/border/strong"],
  },

  "&.Mui-focused": {
    borderColor: semanticColors["color/border/brand"],
  },

  "&.Mui-error": {
    borderColor: semanticColors["color/state/error"],
  },

  "&.Mui-disabled": {
    borderColor: semanticColors["color/border/disabled"],
    backgroundColor: semanticColors["color/bg/subtle"],
    color: semanticColors["color/text/disabled"],
  },

  [`& .${inputBaseClasses.input}`]: {
    boxSizing: "border-box",

    height: "100%",
    minWidth: 0,

    padding: 0,

    color: "inherit",
    font: "inherit",

    /*
     * Явно задаём цвет каретки.
     * Это особенно важно для Telegram WebView на iOS.
     */
    caretColor: semanticColors["color/border/brand"],

    /*
     * Не даём WebKit самостоятельно подменять цвет текста.
     */
    WebkitTextFillColor: "currentColor",

    "&::placeholder": {
      color: semanticColors["color/text/tertiary"],
      opacity: 1,
    },
  },

  [`&.${inputBaseClasses.disabled} .${inputBaseClasses.input}`]: {
    color: semanticColors["color/text/disabled"],
    WebkitTextFillColor: semanticColors["color/text/disabled"],

    "&::placeholder": {
      color: semanticColors["color/text/disabled"],
      opacity: 1,
    },
  },
});

const FieldAdornment = styled(InputAdornment)({
  margin: 0,

  color: semanticColors["color/text/secondary"],

  fontSize: 14,
  lineHeight: "20px",

  "& .MuiSvgIcon-root": {
    color: semanticColors["color/icon/secondary"],
    fontSize: 20,
  },
});

const FieldHelperText = styled(FormHelperText)({
  margin: "6px 0 0",

  color: semanticColors["color/text/secondary"],

  fontSize: 12,
  lineHeight: "18px",

  [`&.${formHelperTextClasses.error}`]: {
    color: semanticColors["color/state/error"],
  },

  [`&.${formHelperTextClasses.disabled}`]: {
    color: semanticColors["color/text/disabled"],
  },
});

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  (
    {
      "aria-describedby": ariaDescribedBy,
      disabled,
      endAdornment,
      error,
      helperText,
      id,
      inputMode,
      label,
      required,
      startAdornment,
      ...props
    },
    ref,
  ) => {
    const generatedId = useId();

    const inputId = id ?? `jobmonitor-field-${generatedId}`;
    const helperTextId = `${inputId}-helper-text`;

    const describedBy =
      [ariaDescribedBy, helperText ? helperTextId : undefined]
        .filter(Boolean)
        .join(" ") || undefined;

    return (
      <FieldControl
        disabled={disabled}
        error={error}
        required={required}
        variant="standard"
      >
        {label && <FieldLabel htmlFor={inputId}>{label}</FieldLabel>}

        <FieldInput
          inputRef={ref}
          id={inputId}
          aria-describedby={describedBy}
          disabled={disabled}
          error={error}
          required={required}
          startAdornment={
            startAdornment ? (
              <FieldAdornment position="start" disablePointerEvents>
                {startAdornment}
              </FieldAdornment>
            ) : undefined
          }
          endAdornment={
            endAdornment ? (
              <FieldAdornment position="end" disablePointerEvents>
                {endAdornment}
              </FieldAdornment>
            ) : undefined
          }
          slotProps={{
            input: inputMode
              ? {
                  inputMode,
                }
              : undefined,
          }}
          {...props}
        />

        {helperText && (
          <FieldHelperText id={helperTextId}>{helperText}</FieldHelperText>
        )}
      </FieldControl>
    );
  },
);

TextField.displayName = "TextField";
