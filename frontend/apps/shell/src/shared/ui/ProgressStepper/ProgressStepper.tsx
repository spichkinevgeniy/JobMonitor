import CheckIcon from "@mui/icons-material/Check";
import { styled } from "@mui/material/styles";

import { semanticColors } from "@jobmonitor/ui";
import type { ProgressStepperProps } from "./ProgressStepper.types";

type StepStatus = "completed" | "active" | "upcoming";
type StepCursor = "clickable" | "default" | "unavailable";

const StepList = styled("ol")({
  boxSizing: "border-box",
  width: "100%",
  display: "flex",
  alignItems: "center",
  margin: 0,
  padding: 0,
  listStyle: "none",
});

const StepItem = styled("li")({
  minWidth: 0,
  display: "flex",
  flex: 1,
  alignItems: "center",
  "&:last-of-type": {
    flex: "0 0 auto",
  },
});

const StepCircle = styled("span", {
  shouldForwardProp: (prop) => prop !== "status" && prop !== "cursorState",
})<{ status: StepStatus; cursorState: StepCursor }>(({ status, cursorState }) => {
  const reached = status !== "upcoming";

  return {
    boxSizing: "border-box",
    width: 28,
    height: 28,
    flex: "0 0 28px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    border: `1px solid ${
      reached
        ? semanticColors["color/border/brand"]
        : semanticColors["color/border/default"]
    }`,
    borderRadius: "50%",
    backgroundColor: reached
      ? semanticColors["color/bg/primary"]
      : semanticColors["color/bg/surface"],
    color: reached
      ? semanticColors["color/text/inverse"]
      : semanticColors["color/text/secondary"],
    cursor:
      cursorState === "clickable"
        ? "inherit"
        : cursorState === "unavailable"
          ? "not-allowed"
          : "default",
    fontSize: 14,
    fontWeight: reached ? 600 : 500,
    lineHeight: 1,
    "& .MuiSvgIcon-root": {
      color: semanticColors["color/icon/inverse"],
      fontSize: 16,
    },
  };
});

const StepButton = styled("button", {
  shouldForwardProp: (prop) => prop !== "status",
})<{ status: StepStatus }>(({ status }) => ({
  boxSizing: "border-box",
  width: 44,
  height: 44,
  flex: "0 0 44px",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  margin: -8,
  padding: 0,
  border: 0,
  borderRadius: "50%",
  backgroundColor: "transparent",
  font: "inherit",
  cursor: "pointer",
  "&:hover > span":
    status === "upcoming"
      ? {
          borderColor: semanticColors["color/border/brand"],
          backgroundColor: semanticColors["color/bg/primary-subtle"],
        }
      : {
          opacity: 0.86,
        },
  "&:focus-visible": {
    outline: `2px solid ${semanticColors["color/border/brand"]}`,
    outlineOffset: 2,
  },
}));

const StepConnector = styled("span", {
  shouldForwardProp: (prop) => prop !== "completed",
})<{ completed: boolean }>(({ completed }) => ({
  height: 2,
  minWidth: 8,
  flex: 1,
  marginInline: 8,
  borderRadius: 999,
  backgroundColor: completed
    ? semanticColors["color/bg/primary"]
    : semanticColors["color/border/default"],
}));

const VisuallyHidden = styled("span")({
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
  border: 0,
});

const normalizeTotalSteps = (totalSteps: number) =>
  Number.isFinite(totalSteps) ? Math.max(1, Math.trunc(totalSteps)) : 1;

const normalizeCurrentStep = (currentStep: number, totalSteps: number) => {
  const finiteCurrentStep = Number.isFinite(currentStep)
    ? Math.trunc(currentStep)
    : 1;

  return Math.min(totalSteps, Math.max(1, finiteCurrentStep));
};

export const ProgressStepper = ({
  currentStep,
  totalSteps,
  maxVisitedStep,
  "aria-label": ariaLabel = "Прогресс",
  onStepClick,
}: ProgressStepperProps) => {
  const safeTotalSteps = normalizeTotalSteps(totalSteps);
  const safeCurrentStep = normalizeCurrentStep(currentStep, safeTotalSteps);
  const safeMaxVisitedStep = normalizeCurrentStep(
    maxVisitedStep ?? safeCurrentStep,
    safeTotalSteps,
  );

  return (
    <StepList aria-label={ariaLabel}>
      {Array.from({ length: safeTotalSteps }, (_, index) => {
        const stepNumber = index + 1;
        const status: StepStatus =
          stepNumber < safeCurrentStep
            ? "completed"
            : stepNumber === safeCurrentStep
              ? "active"
              : "upcoming";
        const isClickable =
          Boolean(onStepClick) &&
          stepNumber !== safeCurrentStep &&
          stepNumber <= safeMaxVisitedStep;
        const cursorState: StepCursor = isClickable
          ? "clickable"
          : onStepClick && stepNumber > safeMaxVisitedStep
            ? "unavailable"
            : "default";

        return (
          <StepItem
            key={stepNumber}
            aria-current={status === "active" ? "step" : undefined}
          >
            {isClickable ? (
              <StepButton
                type="button"
                status={status}
                aria-label={`Перейти к шагу ${stepNumber}`}
                onClick={() => onStepClick?.(stepNumber)}
              >
                <StepCircle
                  status={status}
                  cursorState={cursorState}
                  aria-hidden="true"
                >
                  {status === "completed" ? <CheckIcon /> : stepNumber}
                </StepCircle>
              </StepButton>
            ) : (
              <>
                <StepCircle
                  status={status}
                  cursorState={cursorState}
                  aria-hidden="true"
                >
                  {status === "completed" ? <CheckIcon /> : stepNumber}
                </StepCircle>

                <VisuallyHidden>
                  {status === "completed"
                    ? `Шаг ${stepNumber} выполнен`
                    : status === "active"
                      ? `Шаг ${stepNumber}, текущий`
                      : `Шаг ${stepNumber}`}
                </VisuallyHidden>
              </>
            )}

            {stepNumber < safeTotalSteps && (
              <StepConnector
                completed={stepNumber < safeCurrentStep}
                aria-hidden="true"
              />
            )}
          </StepItem>
        );
      })}
    </StepList>
  );
};
