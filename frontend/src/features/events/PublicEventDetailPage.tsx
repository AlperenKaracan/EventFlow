import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'

import {
  createReservationIntent,
  fetchActiveReservationForEvent,
  reserveEvent,
} from '../../api/attendee'
import { ApiError } from '../../api/errors'
import { fetchPublicEvent } from '../../api/publicEvents'
import { designTokens } from '../../app/theme'
import { useAuth } from '../../auth/authContext'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { EventDateTime } from '../../shared/ui/EventDateTime'
import { Surface } from '../../shared/ui/Surface'
import { getCategoryAccent } from './categoryAccent'

function DetailItem({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <Box>
      <Typography color="text.secondary" variant="overline">
        {label}
      </Typography>
      <Box sx={{ mt: 0.4 }}>{children}</Box>
    </Box>
  )
}

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
  const activeReservationQuery = useQuery({
    queryKey: ['my-reservations', 'active-event', eventId],
    queryFn: () => fetchActiveReservationForEvent(eventId),
    enabled:
      auth.session.status === 'authenticated' &&
      auth.session.user.role === 'attendee',
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

  if (eventQuery.isPending) {
    return (
      <Container maxWidth="lg">
        <LoadingState label="Etkinlik yükleniyor" />
      </Container>
    )
  }
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
  const reserveDisabled =
    event.availableCapacity === 0 ||
    activeReservationQuery.isPending ||
    reserveMutation.isPending ||
    reserveMutation.isSuccess
  const hasActiveReservation =
    reserveMutation.isSuccess || Boolean(activeReservationQuery.data)

  return (
    <Container
      component="main"
      maxWidth={false}
      sx={{
        maxWidth: designTokens.layout.contentMaxWidth,
        py: { xs: 3, md: 6 },
      }}
    >
      <Button
        component={Link}
        to="/"
        color="inherit"
        sx={{ color: 'text.secondary', mb: 3 }}
      >
        ← Etkinliklere dön
      </Button>

      <Box
        sx={{
          display: 'grid',
          gap: { xs: 3, lg: 4 },
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'minmax(0, 1.7fr) minmax(320px, 0.75fr)',
          },
        }}
      >
        <Stack sx={{ gap: 3 }}>
          <Surface
            component="section"
            sx={{
              borderColor: accent.border,
              overflow: 'hidden',
              p: { xs: 3, md: 5 },
              position: 'relative',
              '&::before': {
                backgroundColor: accent.foreground,
                content: '""',
                height: 3,
                inset: '0 0 auto',
                position: 'absolute',
              },
            }}
          >
            <Stack
              direction="row"
              sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1.25 }}
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
              <Typography color="text.secondary" variant="overline">
                ETKİNLİK DETAYI
              </Typography>
            </Stack>
            <Typography
              component="h1"
              variant="h2"
              sx={{ maxWidth: 820, mt: 3 }}
            >
              {event.title}
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gap: 3,
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'minmax(0, 1.5fr) minmax(180px, 1fr)',
                },
                mt: 4,
              }}
            >
              <DetailItem label="Tarih ve saat">
                <EventDateTime
                  startsAt={event.startsAt}
                  timeZone={event.timezone}
                />
              </DetailItem>
              <DetailItem label="Konum">
                <Typography sx={{ fontWeight: 760 }}>
                  {event.location}
                </Typography>
              </DetailItem>
            </Box>
          </Surface>

          <Surface
            component="section"
            aria-labelledby="about-event"
            sx={{ p: { xs: 3, md: 5 } }}
          >
            <Typography id="about-event" component="h2" variant="h4">
              Etkinlik hakkında
            </Typography>
            <Typography
              color="text.secondary"
              sx={{ fontSize: { md: 17 }, mt: 2.5, whiteSpace: 'pre-wrap' }}
            >
              {event.description}
            </Typography>
          </Surface>
        </Stack>

        <Box>
          <Surface
            component="aside"
            aria-label="Rezervasyon özeti"
            sx={{ p: 3, position: { lg: 'sticky' }, top: { lg: 96 } }}
          >
            <Stack
              direction="row"
              sx={{ alignItems: 'center', justifyContent: 'space-between' }}
            >
              <Typography component="h2" variant="h6">
                Kontenjan
              </Typography>
              <Chip
                label={
                  event.availableCapacity > 0
                    ? `${event.availableCapacity} yer kaldı`
                    : 'Kontenjan dolu'
                }
                color={event.availableCapacity > 0 ? 'success' : 'error'}
                size="small"
                variant="outlined"
              />
            </Stack>
            <Typography color="text.secondary" variant="body2" sx={{ mt: 2 }}>
              {event.reservedCount} / {event.capacity} yer ayrıldı
            </Typography>
            <LinearProgress
              aria-label={`Doluluk oranı yüzde ${occupancy}`}
              value={occupancy}
              variant="determinate"
              sx={{ height: 7, mt: 1 }}
            />
            <Divider sx={{ my: 3 }} />

            {hasActiveReservation ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                Rezervasyonun hazır. Etkinlikteki yerin senin için ayrıldı.
              </Alert>
            ) : null}
            {reserveMutation.isError ? (
              <ErrorState
                error={reserveMutation.error}
                onRetry={() =>
                  reserveMutation.variables &&
                  reserveMutation.mutate(reserveMutation.variables)
                }
              />
            ) : null}

            {auth.session.status === 'anonymous' ? (
              <>
                <Typography
                  color="text.secondary"
                  variant="body2"
                  sx={{ mb: 2 }}
                >
                  Yer ayırmak ve rezervasyonunu yönetmek için hesabına giriş
                  yap.
                </Typography>
                <Button
                  component={Link}
                  to="/login"
                  fullWidth
                  variant="contained"
                >
                  Giriş yap ve yer ayır
                </Button>
              </>
            ) : auth.session.status === 'authenticated' &&
              auth.session.user.role === 'attendee' ? (
              activeReservationQuery.isError ? (
                <ErrorState
                  error={activeReservationQuery.error}
                  onRetry={() => void activeReservationQuery.refetch()}
                />
              ) : hasActiveReservation ? (
                <Button
                  component={Link}
                  to="/attendee/reservations"
                  fullWidth
                  variant="outlined"
                >
                  Rezervasyonumu görüntüle
                </Button>
              ) : (
                <Button
                  fullWidth
                  variant="contained"
                  disabled={reserveDisabled}
                  onClick={() =>
                    reserveMutation.mutate(createReservationIntent(event.id))
                  }
                >
                  {event.availableCapacity === 0
                    ? 'Kontenjan dolu'
                    : activeReservationQuery.isPending
                      ? 'Rezervasyon kontrol ediliyor...'
                      : reserveMutation.isPending
                        ? 'Yer ayrılıyor...'
                        : 'Yerimi ayır'}
                </Button>
              )
            ) : (
              <EmptyState
                title="Katılımcı hesabı gerekli"
                description="Organizatör hesabıyla rezervasyon oluşturulamaz."
              />
            )}
            {!hasActiveReservation ? (
              <Typography
                color="text.secondary"
                variant="caption"
                sx={{ display: 'block', mt: 2, textAlign: 'center' }}
              >
                Rezervasyonunu daha sonra hesabından iptal edebilirsin.
              </Typography>
            ) : null}
          </Surface>
        </Box>
      </Box>
    </Container>
  )
}
