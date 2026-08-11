import { Box } from "@mui/material";
import { useLayoutEffect, useRef } from "react";

import { SpecialtyStep } from "@/features/search-profile-form/ui/steps/SpecialtyStep";

interface AuditCaseProps {
  id: string;
  selector: string;
  ignoreSpacingFields?: string[];
}

const AuditCase = ({
  id,
  selector,
  ignoreSpacingFields = [],
}: AuditCaseProps) => {
  const caseRef = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    const caseNode = caseRef.current;

    if (!caseNode) {
      return;
    }

    const target = caseNode.querySelector<HTMLElement>(selector);

    if (!target) {
      throw new Error(`Audit target not found for "${id}": ${selector}`);
    }

    target.setAttribute("data-audit-target", "");
    target.setAttribute("data-audit-root", "");
    target.setAttribute("data-audit-content-mode", "none");

    return () => {
      target.removeAttribute("data-audit-target");
      target.removeAttribute("data-audit-root");
      target.removeAttribute("data-audit-content-mode");
    };
  }, [id, selector]);

  return (
    <Box
      ref={caseRef}
      data-audit-case
      data-audit-id={id}
      data-audit-kind="composition"
      data-audit-ignore-spacing={
        ignoreSpacingFields.length > 0
          ? ignoreSpacingFields.join(",")
          : undefined
      }
      sx={{
        width: 420,
      }}
    >
      <SpecialtyStep />
    </Box>
  );
};

const SpecialtyStepPreview = () => (
  <Box
    sx={{
      display: "grid",
      gap: 4,
      justifyContent: "start",
    }}
  >
    <AuditCase id="specialty-step--header" selector="header" />

    <AuditCase
      id="specialty-step--specialties"
      selector='[role="group"][aria-label="Специальности"]'
      ignoreSpacingFields={["gap"]}
    />

    <AuditCase
      id="specialty-step--skills"
      selector='section[aria-labelledby="skills-title"]'
      ignoreSpacingFields={["gap"]}
    />

    <AuditCase id="specialty-step--footer" selector="footer" />
  </Box>
);

export default SpecialtyStepPreview;
