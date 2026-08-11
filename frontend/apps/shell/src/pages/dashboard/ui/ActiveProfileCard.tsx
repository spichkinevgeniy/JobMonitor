import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import MuiChip from "@mui/material/Chip";
import { Box, Button, Typography } from "@mui/material";
import { buttonClasses } from "@mui/material/Button";
import { styled } from "@mui/material/styles";

import { semanticColors } from "@jobmonitor/ui";
import type { ActiveProfileCardProps } from "../DashboardPage.types";
import { SearchStatus } from "./SearchStatus";

const ProfileSkillChip = styled(MuiChip)({
  width: "fit-content",
  maxWidth: "calc(50% - 4px)",
  height: 32,
  border: `1px solid ${semanticColors["color/border/default"]}`,
  borderRadius: 999,
  backgroundColor: semanticColors["color/bg/surface"],
  color: semanticColors["color/text/primary"],
  fontSize: 14,
  fontWeight: 500,
  lineHeight: "20px",

  "& .MuiChip-label": {
    paddingInline: 12,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
});

const maxVisibleSkills = 3;

export const ActiveProfileCard = ({
  profile,
  onEdit,
}: ActiveProfileCardProps) => {
  const visibleSkills = profile.skills.slice(0, maxVisibleSkills);
  const hiddenSkillsCount = profile.skills.length - visibleSkills.length;

  return (
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

        <Button
          className="DashboardProfile-edit"
          variant="text"
          onClick={onEdit}
          endIcon={<ArrowForwardRoundedIcon aria-hidden="true" />}
          sx={{
            gridColumn: 2,
            gridRow: 2,
            justifySelf: "end",

            minWidth: 0,
            minHeight: 32,

            px: 1,
            py: 0,

            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 0.5,

            borderRadius: 2,

            color: semanticColors["color/text/brand"],

            fontSize: 13,
            fontWeight: 600,
            lineHeight: "18px",
            textTransform: "none",

            "&:hover": {
              bgcolor: semanticColors["color/bg/primary-subtle"],
            },

            "&:focus-visible": {
              outline: `2px solid ${semanticColors["color/border/brand"]}`,
              outlineOffset: 2,
            },

            [`& .${buttonClasses.endIcon}`]: {
              margin: 0,
              display: "flex",
              alignItems: "center",
            },

            [`& .${buttonClasses.endIcon} > *:nth-of-type(1)`]: {
              width: 16,
              height: 16,
              fontSize: 16,
            },
          }}
        >
          Изменить
        </Button>

        {profile.searchActive && (
          <Box
            sx={{
              gridColumn: 1,
              gridRow: 2,
              alignSelf: "center",
            }}
          >
            <SearchStatus />
          </Box>
        )}
      </Box>

      <Box sx={{ mt: 1.5 }}>
        {visibleSkills.length > 0 && (
          <Box
            aria-label="Навыки"
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 1,
            }}
          >
            {visibleSkills.map((skill) => (
              <ProfileSkillChip key={skill} label={skill} />
            ))}

            {hiddenSkillsCount > 0 && (
              <ProfileSkillChip
                aria-label={`Ещё ${hiddenSkillsCount} навыков`}
                label={`+${hiddenSkillsCount}`}
              />
            )}
          </Box>
        )}

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
};
