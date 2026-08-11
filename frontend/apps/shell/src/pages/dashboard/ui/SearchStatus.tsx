import { Box, Typography } from '@mui/material'

export const SearchStatus = () => (
  <Box
    role="status"
    sx={{
      width: 'fit-content',
      minHeight: 20,
      display: 'inline-flex',
      alignItems: 'center',
      gap: 0.75,
      color: 'success.main',
    }}
  >
    <Box
      aria-hidden="true"
      sx={{
        width: 6,
        height: 6,
        flexShrink: 0,
        borderRadius: '50%',
        bgcolor: 'success.main',
      }}
    />
    <Typography
      component="span"
      sx={{ fontSize: 12, fontWeight: 600, lineHeight: '16px' }}
    >
      Поиск активен
    </Typography>
  </Box>
)
