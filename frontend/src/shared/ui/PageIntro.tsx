import { Box, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      sx={{
        alignItems: { md: 'flex-end' },
        gap: 3,
        justifyContent: 'space-between',
      }}
    >
      <Box sx={{ maxWidth: 790 }}>
        {eyebrow ? (
          <Typography color="primary.light" variant="overline">
            {eyebrow}
          </Typography>
        ) : null}
        <Typography component="h1" variant="h2" sx={{ mt: eyebrow ? 0.75 : 0 }}>
          {title}
        </Typography>
        {description ? (
          <Typography
            color="text.secondary"
            sx={{ fontSize: { xs: 16, md: 18 }, mt: 1.5 }}
          >
            {description}
          </Typography>
        ) : null}
      </Box>
      {actions ? <Box sx={{ flexShrink: 0 }}>{actions}</Box> : null}
    </Stack>
  )
}
