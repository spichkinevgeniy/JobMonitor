import CheckIcon from "@mui/icons-material/Check";
import MuiButtonBase, { buttonBaseClasses } from "@mui/material/ButtonBase";
import { styled } from "@mui/material/styles";
import { forwardRef } from "react";

import { semanticColors } from "@jobmonitor/ui";
import type {
  SelectionCardLayout,
  SelectionCardProps,
} from "./SelectionCard.types";

interface SelectionCardRootProps {
  selected: boolean;
  layout: SelectionCardLayout;
}

const SelectionCardRoot = styled(MuiButtonBase, {
  shouldForwardProp: (prop) => prop !== "selected" && prop !== "layout",
})<SelectionCardRootProps>(({ layout, selected, theme }) => ({
  boxSizing: "border-box",
  position: "relative",

  width: "100%",
  minWidth: 0,
  maxWidth: "100%",
  minHeight: 72,
  overflow: "hidden",

  display: "flex",
  flexDirection: layout === "vertical" ? "column" : "row",
  alignItems: layout === "vertical" ? "stretch" : "center",
  justifyContent: "flex-start",
  gap: 12,

  padding: 16,

  border: `1px solid ${
    selected
      ? semanticColors["color/border/brand"]
      : semanticColors["color/border/default"]
  }`,

  borderRadius: 12,

  backgroundColor: selected
    ? semanticColors["color/bg/primary-subtle"]
    : semanticColors["color/bg/surface"],

  color: semanticColors["color/text/primary"],
  fontFamily: theme.typography.fontFamily,

  textAlign: "left",
  boxShadow: "none",

  "&:hover": {
    borderColor: selected
      ? semanticColors["color/border/brand"]
      : semanticColors["color/border/strong"],

    backgroundColor: selected
      ? semanticColors["color/bg/primary-subtle"]
      : semanticColors["color/bg/subtle"],
  },

  [`&.${buttonBaseClasses.focusVisible}`]: {
    outline: `2px solid ${semanticColors["color/border/brand"]}`,
    outlineOffset: 2,
  },

  // Leading icon

  "& .SelectionCard-leadingIcon": {
    width: 32,
    height: 32,

    flex: "0 0 32px",
    alignSelf: "flex-start",

    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",

    borderRadius: 8,

    // В selected-состоянии оставляем icon container
    // визуально отделённым от голубого background карточки.
    backgroundColor: selected
      ? semanticColors["color/bg/surface"]
      : semanticColors["color/bg/primary-subtle"],

    color: semanticColors["color/icon/brand"],
  },

  "& .SelectionCard-leadingIcon .MuiSvgIcon-root": {
    fontSize: 20,
  },

  // Content

  "& .SelectionCard-content": {
    minWidth: 0,
    width: layout === "vertical" ? "100%" : "auto",
    maxWidth: "100%",
    flex: layout === "vertical" ? "0 1 auto" : 1,

    // На узких horizontal-карточках даём тексту ещё 2px.
    // Это предотвращает лишний перенос первой строки,
    // не меняя padding/gap самого компонента.
    marginRight: layout === "vertical" ? 0 : -2,
  },

  "& .SelectionCard-title": {
    display: "block",
    paddingRight: layout === "vertical" ? 0 : 28,
    maxWidth: "100%",

    color: "inherit",

    fontSize: 14,
    fontWeight: 600,
    lineHeight: "20px",
    overflowWrap: "break-word",
    wordBreak: "normal",
    whiteSpace: "normal",
  },

  "& .SelectionCard-description": {
    display: "block",
    maxWidth: "100%",

    marginTop: 2,

    color: semanticColors["color/text/secondary"],

    fontSize: 13,
    fontWeight: 400,
    lineHeight: "18px",
    overflowWrap: "break-word",
    wordBreak: "normal",
    whiteSpace: "normal",
  },

  // Selection indicator

  "& .SelectionCard-indicator": {
    boxSizing: "border-box",

    position: "absolute",
    top: 12,
    right: 8,

    width: 20,
    height: 20,

    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",

    border: `1px solid ${
      selected
        ? semanticColors["color/border/brand"]
        : semanticColors["color/border/default"]
    }`,

    borderRadius: "50%",

    backgroundColor: selected
      ? semanticColors["color/bg/primary"]
      : "transparent",

    color: semanticColors["color/icon/inverse"],
  },

  "& .SelectionCard-indicator .MuiSvgIcon-root": {
    fontSize: 14,
  },

  // Disabled

  [`&.${buttonBaseClasses.disabled}`]: {
    borderColor: semanticColors["color/border/disabled"],
    backgroundColor: semanticColors["color/bg/subtle"],
    color: semanticColors["color/text/disabled"],
  },

  [`&.${buttonBaseClasses.disabled} .SelectionCard-leadingIcon`]: {
    backgroundColor: semanticColors["color/bg/disabled"],
    color: semanticColors["color/icon/disabled"],
  },

  [`&.${buttonBaseClasses.disabled} .SelectionCard-description`]: {
    color: semanticColors["color/text/disabled"],
  },

  [`&.${buttonBaseClasses.disabled} .SelectionCard-indicator`]: {
    borderColor: semanticColors["color/border/disabled"],
    backgroundColor: "transparent",
    color: semanticColors["color/icon/disabled"],
  },
}));

export const SelectionCard = forwardRef<HTMLButtonElement, SelectionCardProps>(
  (
    { description, icon, layout = "horizontal", selected, title, ...props },
    ref,
  ) => (
    <SelectionCardRoot
      ref={ref}
      layout={layout}
      selected={selected}
      aria-pressed={selected}
      {...props}
    >
      <span className="SelectionCard-leadingIcon" aria-hidden="true">
        {icon}
      </span>

      <span className="SelectionCard-content">
        <span className="SelectionCard-title">{title}</span>

        {description && (
          <span className="SelectionCard-description">{description}</span>
        )}
      </span>

      <span className="SelectionCard-indicator" aria-hidden="true">
        {selected && <CheckIcon />}
      </span>
    </SelectionCardRoot>
  ),
);

SelectionCard.displayName = "SelectionCard";
