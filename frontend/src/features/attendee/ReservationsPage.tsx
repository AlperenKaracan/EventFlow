import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Container,
  Stack,
  Typography,
} from '@mui/material'

import {
  cancelMyReservation,
  createReservationIntent,
  fetchMyReservations,
  reserveEvent,
} from '../../api/attendee'
import type { ReservationHistoryResponse } from '../../api/generated'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { useCursorPager } from '../events/cursorPager'

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'long',
  timeStyle: 'short',
})

const statusLabels = {
  ACTIVE: 'Aktif',
  CANCELLED_BY_ATTENDEE: 'Siz iptal ettiniz',
  CANCELLED_BY_EVENT: 'Etkinlik iptal edildi',
} as const

export function ReservationsPage() {
  const pager = useCursorPager()
  const queryClient = useQueryClient()
  const reservationsQuery = useQuery({
    queryKey: ['my-reservations', pager.cursor],
    queryFn: () => fetchMyReservations(pager.cursor),
  })
  const refreshReservations = async () => {
    await queryClient.invalidateQueries({ queryKey: ['my-reservations'] })
    await queryClient.invalidateQueries({ queryKey: ['public-event'] })
    await queryClient.invalidateQueries({ queryKey: ['public-events'] })
  }
  const cancelMutation = useMutation({
    mutationFn: cancelMyReservation,
    onSuccess: refreshReservations,
  })
  const rebookMutation = useMutation({
    mutationFn: reserveEvent,
    retry: 1,
    onSuccess: refreshReservations,
  })

  const rebook = (reservation: ReservationHistoryResponse) => {
    rebookMutation.mutate(createReservationIntent(reservation.event.id))
  }

  return (
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 4, md: 7 } }}>
      <Typography
        component="p"
        color="primary.main"
        sx={{ fontSize: '0.78rem', fontWeight: 850, letterSpacing: '0.12em' }}
      >
        KATILIMCI ALANI
      </Typography>
      <Typography component="h1" variant="h2">
        Rezervasyonlarım
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>
        Aktif ve geçmiş rezervasyonlarınızı tek yerde yönetin.
      </Typography>

      {reservationsQuery.isPending ? (
        <LoadingState label="Rezervasyonlar yükleniyor" />
      ) : null}
      {reservationsQuery.isError ? (
        <ErrorState
          error={reservationsQuery.error}
          onRetry={() => void reservationsQuery.refetch()}
        />
      ) : null}
      {cancelMutation.isError ? (
        <Box sx={{ mb: 2 }}>
          <ErrorState
            error={cancelMutation.error}
            onRetry={() => {
              if (cancelMutation.variables) {
                cancelMutation.mutate(cancelMutation.variables)
              }
            }}
          />
        </Box>
      ) : null}
      {rebookMutation.isError ? (
        <Box sx={{ mb: 2 }}>
          <ErrorState
            error={rebookMutation.error}
            onRetry={() => {
              if (rebookMutation.variables) {
                rebookMutation.mutate(rebookMutation.variables)
              }
            }}
          />
        </Box>
      ) : null}
      {rebookMutation.isSuccess ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          Etkinlik için yeniden yer ayırdınız.
        </Alert>
      ) : null}
      {reservationsQuery.data?.items.length === 0 ? (
        <EmptyState
          title="Rezervasyonunuz yok"
          description="Yaklaşan etkinlikleri keşfederek ilk yerinizi ayırın."
        />
      ) : null}

      {reservationsQuery.data?.items.length ? (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          }}
        >
          {reservationsQuery.data.items.map((reservation) => {
            const isCancelledByEvent =
              reservation.status === 'CANCELLED_BY_EVENT'

            return (
              <Card
                key={reservation.id}
                variant="outlined"
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 220,
                }}
              >
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Chip
                    label={statusLabels[reservation.status]}
                    color={
                      reservation.status === 'ACTIVE' ? 'success' : 'default'
                    }
                    size="small"
                  />
                  <Typography
                    component="h2"
                    variant="h6"
                    sx={{ fontWeight: 800, mt: 2 }}
                  >
                    {reservation.event.title}
                  </Typography>
                  <Typography color="text.secondary">
                    {dateFormatter.format(new Date(reservation.event.startsAt))}
                  </Typography>
                  <Typography color="text.secondary">
                    {reservation.event.location}
                  </Typography>
                  {isCancelledByEvent ? (
                    <Alert severity="warning" sx={{ mt: 2.5 }}>
                      Organizatör bu etkinliği iptal etti. Etkinlik detayları
                      artık yayınlanmıyor.
                    </Alert>
                  ) : null}
                </CardContent>
                <CardActions
                  sx={{
                    borderColor: 'divider',
                    borderTop: '1px solid',
                    px: 2.25,
                    py: 1.5,
                  }}
                >
                  {isCancelledByEvent ? (
                    <Button disabled>Etkinlik iptal edildi</Button>
                  ) : (
                    <Link
                      to="/events/$eventId"
                      params={{ eventId: reservation.event.id }}
                      style={{ textDecoration: 'none' }}
                    >
                      <Box
                        component="span"
                        sx={{
                          alignItems: 'center',
                          borderRadius: 2,
                          color: 'primary.main',
                          display: 'inline-flex',
                          fontSize: '0.875rem',
                          fontWeight: 750,
                          minHeight: 40,
                          px: 1.5,
                          '&:hover': {
                            bgcolor: 'rgba(167, 139, 250, 0.08)',
                          },
                        }}
                      >
                        Etkinliği incele
                      </Box>
                    </Link>
                  )}
                  {reservation.status === 'ACTIVE' ? (
                    <Button
                      color="error"
                      disabled={cancelMutation.isPending}
                      onClick={() => cancelMutation.mutate(reservation.id)}
                    >
                      Rezervasyonu iptal et
                    </Button>
                  ) : reservation.status === 'CANCELLED_BY_ATTENDEE' &&
                    reservation.event.status === 'ACTIVE' ? (
                    <Button
                      disabled={rebookMutation.isPending}
                      onClick={() => rebook(reservation)}
                    >
                      Yeniden yer ayır
                    </Button>
                  ) : null}
                </CardActions>
              </Card>
            )
          })}
        </Box>
      ) : null}

      {reservationsQuery.data?.items.length ? (
        <Stack
          direction="row"
          sx={{ alignItems: 'center', gap: 2, justifyContent: 'center', mt: 5 }}
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
            disabled={!reservationsQuery.data.nextCursor}
            onClick={() =>
              reservationsQuery.data.nextCursor &&
              pager.goForward(reservationsQuery.data.nextCursor)
            }
          >
            Sonraki
          </Button>
        </Stack>
      ) : null}
    </Container>
  )
}
