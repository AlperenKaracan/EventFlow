import { Link } from '@tanstack/react-router'
import {
  Button,
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
        display: 'flex',
        flexDirection: 'column',
        minHeight: 250,
        overflow: 'hidden',
        position: 'relative',
        transition: 'transform 180ms ease, box-shadow 180ms ease',
        '&::before': {
          backgroundColor: accent.foreground,
          content: '""',
          height: 4,
          inset: '0 0 auto',
          position: 'absolute',
        },
        '&:hover': {
          boxShadow: `0 22px 52px ${accent.glow}`,
          transform: 'translateY(-4px)',
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
          >
            {event.availableCapacity > 0
              ? `${event.availableCapacity} yer kaldı`
              : 'Kontenjan dolu'}
          </Typography>
        </Stack>
        <Typography
          component="h3"
          variant="h5"
          sx={{ fontWeight: 820, lineHeight: 1.2, mt: 3 }}
        >
          {event.title}
        </Typography>
        <Typography sx={{ color: 'text.primary', fontWeight: 700, mt: 2 }}>
          {dateFormatter.format(new Date(event.startsAt))}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          {event.location}
        </Typography>
      </CardContent>
      <CardActions sx={{ px: 2.25, pb: 2.25 }}>
        <Link to="/events/$eventId" params={{ eventId: event.id }}>
          <Button component="span" variant="outlined">
            Ayrıntıları gör →
          </Button>
        </Link>
      </CardActions>
    </Card>
  )
}
