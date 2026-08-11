import { Link } from '@tanstack/react-router'
import {
  Box,
  Card,
  Chip,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'

import type { PublicEventResponse } from '../../api/generated'
import {
  eventDateParts,
  formatShortEventDateTime,
} from '../../shared/eventTime'
import { getCategoryAccent } from './categoryAccent'

export function EventCard({ event }: { event: PublicEventResponse }) {
  const accent = getCategoryAccent(event.category.slug)
  const date = eventDateParts(event.startsAt, event.timezone)
  const occupancy = Math.min(
    100,
    Math.round((event.reservedCount / event.capacity) * 100),
  )

  return (
    <Card
      component="article"
      variant="outlined"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 340,
        overflow: 'hidden',
        position: 'relative',
        transition:
          'border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease',
        '&::before': {
          backgroundColor: accent.foreground,
          content: '""',
          height: 3,
          inset: '0 0 auto',
          position: 'absolute',
        },
        '&:hover': {
          borderColor: accent.border,
          boxShadow: `0 22px 54px ${accent.glow}`,
          transform: 'translateY(-3px)',
        },
        '&:focus-within': { borderColor: accent.foreground },
      }}
    >
      <Link
        to="/events/$eventId"
        params={{ eventId: event.id }}
        aria-label="Etkinliği incele"
        style={{
          color: 'inherit',
          display: 'flex',
          flex: 1,
          textDecoration: 'none',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flex: 1,
            flexDirection: 'column',
            p: 3,
          }}
        >
          <Stack
            direction="row"
            sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}
          >
            <Box
              aria-hidden="true"
              sx={{
                alignItems: 'center',
                bgcolor: accent.background,
                border: '1px solid',
                borderColor: accent.border,
                borderRadius: 2.5,
                display: 'flex',
                flexDirection: 'column',
                minWidth: 58,
                px: 1,
                py: 1,
              }}
            >
              <Typography
                sx={{
                  color: accent.foreground,
                  fontSize: 11,
                  fontWeight: 850,
                  letterSpacing: '0.08em',
                }}
              >
                {date.month}
              </Typography>
              <Typography
                sx={{ fontSize: 25, fontWeight: 850, lineHeight: 1.05 }}
              >
                {date.day}
              </Typography>
            </Box>
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
          </Stack>

          <Typography component="h2" variant="h5" sx={{ mt: 3 }}>
            {event.title}
          </Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 1.25 }}>
            {formatShortEventDateTime(event.startsAt, event.timezone)}
          </Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>
            {event.location}
          </Typography>

          <Box sx={{ flexGrow: 1 }} />
          <Stack
            direction="row"
            sx={{
              alignItems: 'center',
              justifyContent: 'space-between',
              mt: 3,
            }}
          >
            <Typography
              color={
                event.availableCapacity > 0 ? 'success.main' : 'error.main'
              }
              variant="caption"
              sx={{ fontWeight: 800 }}
            >
              {event.availableCapacity > 0
                ? `${event.availableCapacity} yer kaldı`
                : 'Kontenjan dolu'}
            </Typography>
            <Typography
              color="primary.light"
              variant="body2"
              sx={{ fontWeight: 780 }}
            >
              Detayları gör{' '}
              <Box component="span" aria-hidden="true">
                →
              </Box>
            </Typography>
          </Stack>
          <LinearProgress
            aria-label={`Kontenjanın yüzde ${occupancy} kadarı dolu`}
            color={event.availableCapacity > 0 ? 'primary' : 'error'}
            value={occupancy}
            variant="determinate"
            sx={{ height: 4, mt: 1.5 }}
          />
        </Box>
      </Link>
    </Card>
  )
}
