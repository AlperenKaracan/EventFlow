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

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'long',
  timeStyle: 'short',
})

export function EventCard({ event }: { event: PublicEventResponse }) {
  return (
    <Card
      component="article"
      variant="outlined"
      sx={{ display: 'flex', flexDirection: 'column' }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Stack
          direction="row"
          sx={{ alignItems: 'center', gap: 1, justifyContent: 'space-between' }}
        >
          <Chip
            label={event.category.name}
            size="small"
            color="primary"
            variant="outlined"
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
        <Typography component="h2" variant="h6" sx={{ mt: 2, fontWeight: 800 }}>
          {event.title}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {dateFormatter.format(new Date(event.startsAt))}
        </Typography>
        <Typography color="text.secondary">{event.location}</Typography>
      </CardContent>
      <CardActions>
        <Link to="/events/$eventId" params={{ eventId: event.id }}>
          <Button component="span">Ayrıntıları gör</Button>
        </Link>
      </CardActions>
    </Card>
  )
}
