import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import { Box, ButtonBase, Typography } from "@mui/material";
import { buttonBaseClasses } from "@mui/material/ButtonBase";
import { semanticColors } from "@jobmonitor/ui";

import type { SearchProfile } from "../model/types";
import { SearchStatus } from "./SearchStatus";
import { SkillPreview } from "./SkillPreview";

interface ActiveProfileCardProps {
  profile: SearchProfile;
  onEdit: () => void;
}

export const ActiveProfileCard = ({
  profile,
  onEdit,
}: ActiveProfileCardProps) => (
  <Box
    component="section"
    aria-labelledby="active-profile-title"
    sx={{
      p: 1.75,
      border: 1,
      borderColor: "divider",
      borderRadius: 3,
      bgcolor: "background.paper",
    }}
  >
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) auto",
        alignItems: "start",
        columnGap: 1,
        rowGap: 0.25,
      }}
    >
      <Typography
        className="DashboardProfile-title"
        id="active-profile-title"
        component="h2"
        sx={{
          color: "text.primary",
          gridColumn: "1 / -1",
          fontSize: 20,
          fontWeight: 700,
          lineHeight: "28px",
          overflowWrap: "break-word",
          wordBreak: "normal",
        }}
      >
        {profile.specialization}
      </Typography>

      <ButtonBase
        className="DashboardProfile-edit"
        onClick={onEdit}
        sx={{
          gridColumn: 2,
          gridRow: 2,
          minHeight: 32,
          flexShrink: 0,
          display: "inline-flex",
          alignItems: "center",
          justifySelf: "end",
          gap: 0.5,
          px: 1,
          mr: -1,
          borderRadius: 2,
          color: semanticColors["color/text/brand"],
          fontSize: 13,
          fontWeight: 600,
          lineHeight: "18px",
          "&:hover": {
            bgcolor: semanticColors["color/bg/primary-subtle"],
          },
          [`&.${buttonBaseClasses.focusVisible}`]: {
            outline: `2px solid ${semanticColors["color/border/brand"]}`,
            outlineOffset: 2,
          },
          "& .MuiSvgIcon-root": {
            display: "block",
            flexShrink: 0,
            fontSize: 16,
            transform: "translateY(-0.5px)",
          },
        }}
      >
        Изменить
        <ArrowForwardRoundedIcon aria-hidden="true" />
      </ButtonBase>

      {profile.searchActive && (
        <Box sx={{ gridColumn: 1, gridRow: 2, alignSelf: "center" }}>
          <SearchStatus />
        </Box>
      )}
    </Box>

    <Box sx={{ mt: 1.5 }}>
      <SkillPreview skills={profile.skills} />

      <Typography
        aria-label="Параметры профиля"
        sx={{
          mt: 1.5,
          color: "text.secondary",
          fontSize: 13,
          fontWeight: 500,
          lineHeight: "20px",
          overflowWrap: "break-word",
          whiteSpace: "normal",
        }}
      >
        {profile.workFormat} · {profile.level} · {profile.salary}
      </Typography>
    </Box>
  </Box>
);
