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
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'

import { fetchPublicEvent } from '../../api/publicEvents'
import { createReservationIntent, reserveEvent } from '../../api/attendee'
import { ApiError } from '../../api/errors'
import { useAuth } from '../../auth/authContext'
import { ErrorState, LoadingState } from '../../shared/AsyncState'
import { getCategoryAccent } from './categoryAccent'

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
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.code === 'RESOURCE_NOT_FOUND') &&
      failureCount < 1,
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
    const isUnavailable =
      eventQuery.error instanceof ApiError &&
      eventQuery.error.code === 'RESOURCE_NOT_FOUND'

    return (
      <Container component="main" maxWidth="md" sx={{ py: 8 }}>
        <ErrorState
          error={eventQuery.error}
          title={isUnavailable ? 'Etkinlik artık görüntülenemiyor' : undefined}
          description={
            isUnavailable
              ? 'Etkinlik organizatör tarafından iptal edilmiş veya yayından kaldırılmış olabilir.'
              : undefined
          }
          onRetry={isUnavailable ? undefined : () => void eventQuery.refetch()}
        />
        <Button component={Link} to="/" sx={{ mt: 2 }}>
          ← Etkinliklere dön
        </Button>
      </Container>
    )
  }

  const event = eventQuery.data
  const accent = getCategoryAccent(event.category.slug)
  const occupancy = Math.min(
    100,
    Math.round((event.reservedCount / event.capacity) * 100),
  )

  return (
    <Container component="main" maxWidth="md" sx={{ py: { xs: 4, md: 8 } }}>
      <Button component={Link} to="/" sx={{ mb: 3 }}>
        ← Etkinliklere dön
      </Button>
      <Card
        variant="outlined"
        sx={{
          overflow: 'hidden',
          position: 'relative',
          '&::before': {
            backgroundColor: accent.foreground,
            content: '""',
            height: 4,
            inset: '0 0 auto',
            position: 'absolute',
          },
        }}
      >
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack
            direction="row"
            sx={{ flexWrap: 'wrap', gap: 2, justifyContent: 'space-between' }}
          >
            <Chip
              label={event.category.name}
              variant="outlined"
              sx={{
                backgroundColor: accent.background,
                borderColor: accent.border,
                color: accent.foreground,
              }}
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
          <Typography
            component="p"
            color="text.secondary"
            sx={{
              fontSize: '0.76rem',
              fontWeight: 800,
              letterSpacing: '0.12em',
              mt: 4,
            }}
          >
            ETKİNLİK DETAYI
          </Typography>
          <Typography component="h1" variant="h2" sx={{ mt: 1 }}>
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
            <LinearProgress
              aria-label="Doluluk oranı"
              value={occupancy}
              variant="determinate"
              sx={{ borderRadius: 999, height: 6, mt: 1.25 }}
            />
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
