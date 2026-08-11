import { Box, Typography } from '@mui/material'

export const VacanciesPlaceholder = () => (
  <Box component="section" aria-labelledby="new-vacancies-title">
    <Typography
      id="new-vacancies-title"
      component="h2"
      sx={{
        color: 'text.primary',
        fontSize: 20,
        fontWeight: 700,
        lineHeight: '28px',
      }}
    >
      Новые вакансии
    </Typography>

    <Box
      sx={{
        mt: 1,
        py: 1.5,
      }}
    >
      <Typography
        sx={{ color: 'text.primary', fontSize: 15, fontWeight: 600 }}
      >
        Пока новых вакансий нет
      </Typography>
      <Typography
        sx={{
          mt: 0.5,
          maxWidth: 340,
          color: 'text.secondary',
          fontSize: 14,
          lineHeight: '20px',
        }}
      >
        Мы покажем их здесь, как только найдём подходящие предложения.
      </Typography>
    </Box>
  </Box>
)
