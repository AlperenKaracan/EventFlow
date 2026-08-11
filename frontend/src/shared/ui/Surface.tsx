import { Box, Paper, Typography } from '@mui/material'
import type { PaperProps } from '@mui/material'
import type { ReactNode } from 'react'

export function Surface({ children, sx, ...props }: PaperProps) {
  return (
    <Paper
      elevation={0}
      variant="outlined"
      sx={{ p: { xs: 2, sm: 3 }, ...sx }}
      {...props}
    >
      {children}
    </Paper>
  )
}

export function StatCard({
  label,
  value,
  hint,
  accent = 'primary.main',
}: {
  label: string
  value: ReactNode
  hint?: string
  accent?: string
}) {
  return (
    <Surface sx={{ minHeight: 132, position: 'relative', overflow: 'hidden' }}>
      <Box
        sx={{
          backgroundColor: accent,
          height: 3,
          inset: '0 0 auto',
          position: 'absolute',
        }}
      />
      <Typography
        color="text.secondary"
        variant="body2"
        sx={{ fontWeight: 700 }}
      >
        {label}
      </Typography>
      <Typography
        component="p"
        sx={{ fontSize: 'clamp(1.75rem, 4vw, 2.3rem)', fontWeight: 820, mt: 1 }}
      >
        {value}
      </Typography>
      {hint ? (
        <Typography color="text.secondary" variant="caption">
          {hint}
        </Typography>
      ) : null}
    </Surface>
  )
}
