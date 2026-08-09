import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Button,
  Container,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'

import { fetchEventAttendees, fetchOwnedEvent } from '../../api/organizer'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { useCursorPager } from '../events/cursorPager'

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function OrganizerAttendeesPage({ eventId }: { eventId: string }) {
  const pager = useCursorPager()
  const eventQuery = useQuery({
    queryKey: ['owned-event', eventId],
    queryFn: () => fetchOwnedEvent(eventId),
  })
  const attendeesQuery = useQuery({
    queryKey: ['event-attendees', eventId, pager.cursor],
    queryFn: () => fetchEventAttendees(eventId, pager.cursor),
  })

  if (eventQuery.isPending || attendeesQuery.isPending)
    return <LoadingState label="Katılımcılar yükleniyor" />
  const error = eventQuery.error ?? attendeesQuery.error
  if (error)
    return (
      <Container component="main" maxWidth="md" sx={{ py: 8 }}>
        <ErrorState
          error={error}
          onRetry={() => {
            void eventQuery.refetch()
            void attendeesQuery.refetch()
          }}
        />
      </Container>
    )

  if (!eventQuery.data || !attendeesQuery.data) {
    return <LoadingState label="Katılımcılar yükleniyor" />
  }

  const event = eventQuery.data
  const attendees = attendeesQuery.data

  return (
    <Container component="main" maxWidth="md" sx={{ py: { xs: 4, md: 7 } }}>
      <Button component={Link} to="/organizer/events">
        ← Etkinliklerime dön
      </Button>
      <Typography
        component="p"
        color="primary.main"
        sx={{
          fontSize: '0.78rem',
          fontWeight: 850,
          letterSpacing: '0.12em',
          mt: 3,
        }}
      >
        KATILIMCI LİSTESİ
      </Typography>
      <Typography component="h1" variant="h2" sx={{ mt: 1 }}>
        {event.title} katılımcıları
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1 }}>
        {event.reservedCount} aktif rezervasyon
      </Typography>
      {attendees.items.length === 0 ? (
        <EmptyState
          title="Henüz katılımcı yok"
          description="Rezervasyon yapan katılımcılar burada görünecek."
        />
      ) : (
        <List
          sx={{
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            mt: 4,
          }}
        >
          {attendees.items.map((attendee) => (
            <ListItem key={attendee.reservationId} divider>
              <ListItemText
                primary={attendee.fullName}
                secondary={`${attendee.email} · ${dateFormatter.format(new Date(attendee.reservedAt))}`}
              />
            </ListItem>
          ))}
        </List>
      )}
      {attendees.items.length ? (
        <Stack
          direction="row"
          sx={{ alignItems: 'center', gap: 2, justifyContent: 'center', mt: 4 }}
        >
          <Button
            variant="outlined"
            disabled={!pager.canGoBack}
            onClick={pager.goBack}
          >
            Önceki
          </Button>
          <Typography>Sayfa {pager.page}</Typography>
          <Button
            variant="outlined"
            disabled={!attendees.nextCursor}
            onClick={() =>
              attendees.nextCursor && pager.goForward(attendees.nextCursor)
            }
          >
            Sonraki
          </Button>
        </Stack>
      ) : null}
    </Container>
  )
}
