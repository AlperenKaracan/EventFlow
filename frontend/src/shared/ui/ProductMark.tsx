import { Box, Typography } from '@mui/material'
import type { SxProps, Theme } from '@mui/material/styles'

export function ProductMark({
  compact = false,
  sx,
}: {
  compact?: boolean
  sx?: SxProps<Theme>
}) {
  return (
    <Box
      sx={{ alignItems: 'center', display: 'inline-flex', gap: 1.15, ...sx }}
    >
      <Box
        aria-hidden="true"
        sx={{
          alignItems: 'center',
          backgroundColor: 'primary.main',
          borderRadius: '10px 10px 10px 3px',
          color: 'primary.contrastText',
          display: 'inline-flex',
          fontSize: 13,
          fontWeight: 950,
          height: 34,
          justifyContent: 'center',
          letterSpacing: '-0.06em',
          width: 34,
        }}
      >
        EF
      </Box>
      {!compact ? (
        <Typography
          component="span"
          sx={{
            fontSize: '1.08rem',
            fontWeight: 880,
            letterSpacing: '-0.04em',
          }}
        >
          EventFlow
        </Typography>
      ) : null}
    </Box>
  )
}
