import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from '@mui/material'
import { useState } from 'react'

import {
  cancelMyReservation,
  createReservationIntent,
  fetchMyReservations,
  reserveEvent,
} from '../../api/attendee'
import type { ReservationHistoryResponse } from '../../api/generated'
import { designTokens } from '../../app/theme'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { EventDateTime } from '../../shared/ui/EventDateTime'
import { PageIntro } from '../../shared/ui/PageIntro'
import { StatCard, Surface } from '../../shared/ui/Surface'
import { useCursorPager } from '../events/cursorPager'

const statusLabels = {
  ACTIVE: 'Aktif',
  CANCELLED_BY_ATTENDEE: 'Sizin tarafınızdan iptal edildi',
  CANCELLED_BY_EVENT: 'Organizatör tarafından iptal edildi',
} as const

const statusColors = {
  ACTIVE: 'success' as const,
  CANCELLED_BY_ATTENDEE: 'default' as const,
  CANCELLED_BY_EVENT: 'warning' as const,
}

export function ReservationsPage() {
  const pager = useCursorPager()
  const queryClient = useQueryClient()
  const [cancelTarget, setCancelTarget] =
    useState<ReservationHistoryResponse | null>(null)
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
    onSuccess: async () => {
      setCancelTarget(null)
      await refreshReservations()
    },
  })
  const rebookMutation = useMutation({
    mutationFn: reserveEvent,
    retry: 1,
    onSuccess: refreshReservations,
  })
  const items = reservationsQuery.data?.items ?? []
  const activeCount = items.filter(
    (reservation) => reservation.status === 'ACTIVE',
  ).length
  const cancelledCount = items.length - activeCount

  const rebook = (reservation: ReservationHistoryResponse) => {
    rebookMutation.mutate(createReservationIntent(reservation.event.id))
  }

  return (
    <Container
      component="main"
      maxWidth={false}
      sx={{
        maxWidth: designTokens.layout.contentMaxWidth,
        py: { xs: 4, md: 7 },
      }}
    >
      <PageIntro
        eyebrow="KATILIMCI ALANI"
        title="Rezervasyonlarım"
        description="Yaklaşan planlarınızı görün, rezervasyon durumlarını takip edin ve değişiklikleri güvenle yönetin."
        actions={
          <Button component={Link} to="/" variant="contained">
            Etkinlik keşfet
          </Button>
        }
      />

      {items.length ? (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
            mt: 4,
          }}
        >
          <StatCard
            label="Bu sayfadaki rezervasyon"
            value={items.length}
            hint={`${pager.page}. sayfa`}
          />
          <StatCard
            label="Aktif"
            value={activeCount}
            accent="success.main"
            hint="Katılım için hazır"
          />
          <StatCard
            label="İptal edilen"
            value={cancelledCount}
            accent="warning.main"
            hint="Geçmiş kayıt"
          />
        </Box>
      ) : null}

      <Box sx={{ mt: 4 }}>
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
              onRetry={() =>
                cancelMutation.variables &&
                cancelMutation.mutate(cancelMutation.variables)
              }
            />
          </Box>
        ) : null}
        {rebookMutation.isError ? (
          <Box sx={{ mb: 2 }}>
            <ErrorState
              error={rebookMutation.error}
              onRetry={() =>
                rebookMutation.variables &&
                rebookMutation.mutate(rebookMutation.variables)
              }
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
            title="Henüz rezervasyonunuz yok"
            description="İlginizi çeken bir etkinliği keşfederek ilk yerinizi ayırabilirsiniz."
            action={
              <Button component={Link} to="/" variant="contained">
                Etkinlikleri keşfet
              </Button>
            }
          />
        ) : null}

        {items.length ? (
          <Stack aria-label="Rezervasyon listesi" sx={{ gap: 2 }}>
            {items.map((reservation) => {
              const isCancelledByEvent =
                reservation.status === 'CANCELLED_BY_EVENT'
              return (
                <Surface
                  component="article"
                  key={reservation.id}
                  sx={{
                    display: 'grid',
                    gap: { xs: 2.5, md: 3 },
                    gridTemplateColumns: {
                      xs: '1fr',
                      md: 'minmax(0, 1.5fr) minmax(250px, 0.8fr) auto',
                    },
                    p: { xs: 2.5, md: 3 },
                  }}
                >
                  <Box>
                    <Chip
                      label={statusLabels[reservation.status]}
                      color={statusColors[reservation.status]}
                      size="small"
                      variant="outlined"
                    />
                    <Typography component="h2" variant="h5" sx={{ mt: 2 }}>
                      {reservation.event.title}
                    </Typography>
                    <Typography
                      color="text.secondary"
                      variant="body2"
                      sx={{ mt: 1 }}
                    >
                      {reservation.event.location}
                    </Typography>
                    {isCancelledByEvent ? (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        Organizatör bu etkinliği iptal etti. Kayıt, rezervasyon
                        geçmişiniz için korunuyor.
                      </Alert>
                    ) : null}
                  </Box>
                  <Box
                    sx={{
                      borderLeft: { md: '1px solid' },
                      borderColor: { md: 'divider' },
                      pl: { md: 3 },
                    }}
                  >
                    <Typography color="text.secondary" variant="overline">
                      ETKİNLİK ZAMANI
                    </Typography>
                    <EventDateTime
                      startsAt={reservation.event.startsAt}
                      timeZone={reservation.event.timezone}
                    />
                  </Box>
                  <Stack
                    sx={{
                      alignItems: { md: 'flex-end' },
                      gap: 1,
                      justifyContent: 'center',
                      minWidth: { md: 175 },
                    }}
                  >
                    {!isCancelledByEvent ? (
                      <Link
                        to="/events/$eventId"
                        params={{ eventId: reservation.event.id }}
                        style={{ textDecoration: 'none', width: '100%' }}
                      >
                        <Box
                          component="span"
                          sx={{
                            alignItems: 'center',
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 3,
                            color: 'primary.light',
                            display: 'inline-flex',
                            fontSize: '0.875rem',
                            fontWeight: 760,
                            justifyContent: 'center',
                            minHeight: 44,
                            px: 2,
                            width: '100%',
                            '&:hover': {
                              borderColor: 'primary.main',
                              bgcolor: 'action.hover',
                            },
                          }}
                        >
                          Etkinliği incele
                        </Box>
                      </Link>
                    ) : (
                      <Button disabled fullWidth>
                        Etkinlik iptal edildi
                      </Button>
                    )}
                    {reservation.status === 'ACTIVE' ? (
                      <Button
                        color="error"
                        disabled={cancelMutation.isPending}
                        onClick={() => setCancelTarget(reservation)}
                        fullWidth
                      >
                        Rezervasyonu iptal et
                      </Button>
                    ) : reservation.status === 'CANCELLED_BY_ATTENDEE' &&
                      reservation.event.status === 'ACTIVE' ? (
                      <Button
                        disabled={rebookMutation.isPending}
                        onClick={() => rebook(reservation)}
                        fullWidth
                      >
                        Yeniden yer ayır
                      </Button>
                    ) : null}
                  </Stack>
                </Surface>
              )
            })}
          </Stack>
        ) : null}
      </Box>

      {items.length ? (
        <Stack
          direction="row"
          sx={{
            alignItems: 'center',
            gap: 1.5,
            justifyContent: 'center',
            mt: 5,
          }}
        >
          <Button
            variant="outlined"
            disabled={!pager.canGoBack}
            onClick={pager.goBack}
          >
            Önceki sayfa
          </Button>
          <Typography color="text.secondary">{pager.page}. sayfa</Typography>
          <Button
            variant="outlined"
            disabled={!reservationsQuery.data?.nextCursor}
            onClick={() =>
              reservationsQuery.data?.nextCursor &&
              pager.goForward(reservationsQuery.data.nextCursor)
            }
          >
            Sonraki sayfa
          </Button>
        </Stack>
      ) : null}

      <Dialog
        open={Boolean(cancelTarget)}
        onClose={() => !cancelMutation.isPending && setCancelTarget(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>Rezervasyonu iptal etmek istiyor musunuz?</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            {cancelTarget?.event.title} için ayırdığınız yer bırakılacak.
            Kontenjan uygunsa daha sonra yeniden yer ayırabilirsiniz.
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Typography color="warning.main" variant="body2">
            Bu işlem etkinliği iptal etmez, yalnızca sizin rezervasyonunuzu
            etkiler.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            color="inherit"
            disabled={cancelMutation.isPending}
            onClick={() => setCancelTarget(null)}
          >
            Vazgeç
          </Button>
          <Button
            color="error"
            variant="contained"
            disabled={!cancelTarget || cancelMutation.isPending}
            onClick={() =>
              cancelTarget && cancelMutation.mutate(cancelTarget.id)
            }
          >
            {cancelMutation.isPending
              ? 'İptal ediliyor...'
              : 'Rezervasyonu iptal et'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
