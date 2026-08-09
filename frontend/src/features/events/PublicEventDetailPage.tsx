import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Box,
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Stack,
  Typography,
} from '@mui/material'

import { fetchPublicEvent } from '../../api/publicEvents'
import { createReservationIntent, reserveEvent } from '../../api/attendee'
import { useAuth } from '../../auth/authContext'
import { ErrorState, LoadingState } from '../../shared/AsyncState'

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'full',
  timeStyle: 'short',
})

export function PublicEventDetailPage({ eventId }: { eventId: string }) {
  const auth = useAuth()
  const queryClient = useQueryClient()
  const eventQuery = useQuery({
    queryKey: ['public-event', eventId],
    queryFn: () => fetchPublicEvent(eventId),
  })
  const reserveMutation = useMutation({
    mutationFn: reserveEvent,
    retry: 1,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['public-event', eventId],
      })
      await queryClient.invalidateQueries({ queryKey: ['public-events'] })
      await queryClient.invalidateQueries({ queryKey: ['my-reservations'] })
    },
  })

  if (eventQuery.isPending) return <LoadingState label="Etkinlik yükleniyor" />
  if (eventQuery.isError) {
    return (
      <Container component="main" maxWidth="md" sx={{ py: 8 }}>
        <ErrorState
          error={eventQuery.error}
          onRetry={() => void eventQuery.refetch()}
        />
      </Container>
    )
  }

  const event = eventQuery.data

  return (
    <Container component="main" maxWidth="md" sx={{ py: { xs: 4, md: 8 } }}>
      <Button component={Link} to="/" sx={{ mb: 3 }}>
        ← Etkinliklere dön
      </Button>
      <Card variant="outlined">
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack
            direction="row"
            sx={{ flexWrap: 'wrap', gap: 2, justifyContent: 'space-between' }}
          >
            <Chip
              label={event.category.name}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={
                event.availableCapacity > 0
                  ? `${event.availableCapacity} yer kaldı`
                  : 'Kontenjan dolu'
              }
              color={event.availableCapacity > 0 ? 'success' : 'error'}
            />
          </Stack>
          <Typography component="h1" variant="h1" sx={{ mt: 3 }}>
            {event.title}
          </Typography>
          <Stack sx={{ gap: 1, mt: 3 }}>
            <Typography sx={{ fontWeight: 700 }}>
              {dateFormatter.format(new Date(event.startsAt))}
            </Typography>
            <Typography color="text.secondary">{event.location}</Typography>
            <Typography color="text.secondary">
              Saat dilimi: {event.timezone}
            </Typography>
          </Stack>
          <Divider sx={{ my: 4 }} />
          <Typography component="h2" variant="h5" sx={{ fontWeight: 800 }}>
            Etkinlik hakkında
          </Typography>
          <Typography sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>
            {event.description}
          </Typography>
          <Box sx={{ mt: 4 }}>
            <Typography variant="body2" color="text.secondary">
              {event.reservedCount} / {event.capacity} yer ayrıldı
            </Typography>
          </Box>
          <Box sx={{ mt: 4 }}>
            {reserveMutation.isSuccess ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                Yeriniz ayrıldı. Rezervasyonlarınızdan yönetebilirsiniz.
              </Alert>
            ) : null}
            {reserveMutation.isError ? (
              <ErrorState
                error={reserveMutation.error}
                onRetry={() => {
                  if (reserveMutation.variables)
                    reserveMutation.mutate(reserveMutation.variables)
                }}
              />
            ) : null}
            {auth.session.status === 'anonymous' ? (
              <Button component={Link} to="/login" variant="contained">
                Yer ayırmak için giriş yap
              </Button>
            ) : auth.session.status === 'authenticated' &&
              auth.session.user.role === 'attendee' ? (
              <Button
                variant="contained"
                disabled={
                  event.availableCapacity === 0 ||
                  reserveMutation.isPending ||
                  reserveMutation.isSuccess
                }
                onClick={() =>
                  reserveMutation.mutate(createReservationIntent(event.id))
                }
              >
                {event.availableCapacity === 0
                  ? 'Kontenjan dolu'
                  : reserveMutation.isPending
                    ? 'Yer ayrılıyor…'
                    : 'Yer ayır'}
              </Button>
            ) : null}
          </Box>
        </CardContent>
      </Card>
    </Container>
  )
}
