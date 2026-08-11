import { Link } from '@tanstack/react-router'
import {
  Box,
  Card,
  CardActions,
  CardContent,
  Chip,
  Stack,
  Typography,
} from '@mui/material'

import type { PublicEventResponse } from '../../api/generated'
import { getCategoryAccent } from './categoryAccent'

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'long',
  timeStyle: 'short',
})

export function EventCard({ event }: { event: PublicEventResponse }) {
  const accent = getCategoryAccent(event.category.slug)

  return (
    <Card
      component="article"
      variant="outlined"
      sx={{
        backgroundImage: `linear-gradient(145deg, ${accent.background}, transparent 42%)`,
        display: 'flex',
        flexDirection: 'column',
        minHeight: 270,
        overflow: 'hidden',
        position: 'relative',
        transition:
          'border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease',
        '&::before': {
          backgroundColor: accent.foreground,
          content: '""',
          height: 4,
          inset: '0 0 auto',
          position: 'absolute',
        },
        '&:hover': {
          borderColor: accent.border,
          boxShadow: `0 22px 52px ${accent.glow}`,
          transform: 'translateY(-4px)',
        },
        '&:focus-within': {
          borderColor: accent.foreground,
          boxShadow: `0 0 0 3px ${accent.glow}`,
        },
        '@media (prefers-reduced-motion: reduce)': {
          transition: 'none',
          '&:hover': { transform: 'none' },
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Stack
          direction="row"
          sx={{ alignItems: 'center', gap: 1, justifyContent: 'space-between' }}
        >
          <Chip
            label={event.category.name}
            size="small"
            variant="outlined"
            sx={{
              backgroundColor: accent.background,
              borderColor: accent.border,
              color: accent.foreground,
            }}
          />
          <Typography
            variant="caption"
            color={event.availableCapacity > 0 ? 'success.main' : 'error.main'}
            sx={{ fontWeight: 750 }}
          >
            {event.availableCapacity > 0
              ? `${event.availableCapacity} yer kaldı`
              : 'Kontenjan dolu'}
          </Typography>
        </Stack>
        <Typography
          component="h2"
          variant="h5"
          sx={{ fontWeight: 820, lineHeight: 1.2, mt: 3 }}
        >
          {event.title}
        </Typography>
        <Stack sx={{ gap: 1.5, mt: 2.5 }}>
          <Stack sx={{ gap: 0.25 }}>
            <Typography
              color="text.secondary"
              variant="caption"
              sx={{ fontWeight: 800, letterSpacing: '0.08em' }}
            >
              TARİH
            </Typography>
            <Typography sx={{ color: 'text.primary', fontWeight: 700 }}>
              {dateFormatter.format(new Date(event.startsAt))}
            </Typography>
          </Stack>
          <Stack sx={{ gap: 0.25 }}>
            <Typography
              color="text.secondary"
              variant="caption"
              sx={{ fontWeight: 800, letterSpacing: '0.08em' }}
            >
              KONUM
            </Typography>
            <Typography color="text.secondary">{event.location}</Typography>
          </Stack>
        </Stack>
      </CardContent>
      <CardActions
        sx={{
          borderColor: 'divider',
          borderTop: '1px solid',
          px: 2.25,
          py: 1.6,
        }}
      >
        <Link
          to="/events/$eventId"
          params={{ eventId: event.id }}
          style={{ textDecoration: 'none' }}
        >
          <Box
            component="span"
            sx={{
              alignItems: 'center',
              border: '1px solid',
              borderColor: 'primary.main',
              borderRadius: 2.5,
              color: 'primary.main',
              display: 'inline-flex',
              fontSize: '0.875rem',
              fontWeight: 750,
              gap: 0.75,
              minHeight: 38,
              px: 2,
              transition: 'background-color 150ms ease',
              '&:hover': { bgcolor: 'rgba(167, 139, 250, 0.08)' },
            }}
          >
            Etkinliği incele <span aria-hidden="true">→</span>
          </Box>
        </Link>
      </CardActions>
    </Card>
  )
}
