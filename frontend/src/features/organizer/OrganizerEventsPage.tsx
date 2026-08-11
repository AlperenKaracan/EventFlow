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
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import { useState } from 'react'
import type { ReactNode } from 'react'

import type { OwnerEventResponse } from '../../api/generated'
import { cancelOwnedEvent, fetchOwnedEvents } from '../../api/organizer'
import { designTokens } from '../../app/theme'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { EventDateTime } from '../../shared/ui/EventDateTime'
import { PageIntro } from '../../shared/ui/PageIntro'
import { StatCard, Surface } from '../../shared/ui/Surface'
import { useCursorPager } from '../events/cursorPager'

export function OrganizerEventsPage() {
  const pager = useCursorPager()
  const queryClient = useQueryClient()
  const [eventToCancel, setEventToCancel] = useState<OwnerEventResponse | null>(
    null,
  )
  const eventsQuery = useQuery({
    queryKey: ['owned-events', pager.cursor],
    queryFn: () => fetchOwnedEvents(pager.cursor),
  })
  const cancelMutation = useMutation({
    mutationFn: (event: OwnerEventResponse) =>
      cancelOwnedEvent(event.id, event.version),
    onSuccess: async () => {
      setEventToCancel(null)
      await queryClient.invalidateQueries({ queryKey: ['owned-events'] })
    },
  })
  const items = eventsQuery.data?.items ?? []
  const activeEvents = items.filter((event) => event.status === 'ACTIVE')
  const totalReservations = activeEvents.reduce(
    (sum, event) => sum + event.reservedCount,
    0,
  )
  const totalAvailable = activeEvents.reduce(
    (sum, event) => sum + event.availableCapacity,
    0,
  )

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
        eyebrow="ORGANİZATÖR ÇALIŞMA ALANI"
        title="Etkinliklerim"
        description="Yayınlarınızı, kontenjanları ve katılımcı hareketlerini hızlıca görün; gereken aksiyona doğrudan geçin."
        actions={
          <Button
            component={Link}
            to="/organizer/events/new"
            variant="contained"
          >
            + Yeni etkinlik
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
            label="Aktif etkinlik"
            value={activeEvents.length}
            hint={`${pager.page}. sayfadaki yayınlar`}
          />
          <StatCard
            label="Aktif rezervasyon"
            value={totalReservations}
            accent="success.main"
            hint="Toplam ayrılan yer"
          />
          <StatCard
            label="Kalan kontenjan"
            value={totalAvailable}
            accent="info.main"
            hint="Aktif etkinliklerde"
          />
        </Box>
      ) : null}

      <Box sx={{ mt: 4 }}>
        {eventsQuery.isPending ? (
          <LoadingState label="Etkinlikleriniz yükleniyor" />
        ) : null}
        {eventsQuery.isError ? (
          <ErrorState
            error={eventsQuery.error}
            onRetry={() => void eventsQuery.refetch()}
          />
        ) : null}
        {eventsQuery.data?.items.length === 0 ? (
          <EmptyState
            title="Henüz etkinliğiniz yok"
            description="İlk etkinliğinizi oluşturarak topluluğunuzla buluşmaya başlayın."
            action={
              <Button
                component={Link}
                to="/organizer/events/new"
                variant="contained"
              >
                İlk etkinliğimi oluştur
              </Button>
            }
          />
        ) : null}
        {items.length ? (
          <Box
            sx={{
              display: 'grid',
              gap: 2.5,
              gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' },
            }}
          >
            {items.map((event) => {
              const occupancy = Math.min(
                100,
                Math.round((event.reservedCount / event.capacity) * 100),
              )
              const cancelled = event.status === 'CANCELLED'
              return (
                <Surface
                  component="article"
                  key={event.id}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    p: 0,
                    overflow: 'hidden',
                  }}
                >
                  <Box sx={{ flexGrow: 1, p: 3 }}>
                    <Stack
                      direction="row"
                      sx={{
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Chip
                        label={cancelled ? 'İptal edildi' : 'Yayında'}
                        color={cancelled ? 'default' : 'success'}
                        size="small"
                        variant="outlined"
                      />
                      <Typography color="text.secondary" variant="caption">
                        {cancelled ? 'Salt okunur kayıt' : 'Rezervasyona açık'}
                      </Typography>
                    </Stack>
                    <Typography component="h2" variant="h5" sx={{ mt: 2.5 }}>
                      {event.title}
                    </Typography>
                    <Box
                      sx={{
                        display: 'grid',
                        gap: 2,
                        gridTemplateColumns: { xs: '1fr', sm: '1fr 0.7fr' },
                        mt: 2.5,
                      }}
                    >
                      <EventDateTime
                        startsAt={event.startsAt}
                        timeZone={event.timezone}
                      />
                      <Box>
                        <Typography color="text.secondary" variant="overline">
                          KONUM
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {event.location}
                        </Typography>
                      </Box>
                    </Box>
                    <Divider sx={{ my: 2.5 }} />
                    <Stack
                      direction="row"
                      sx={{
                        alignItems: 'baseline',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 760 }}>
                        {event.reservedCount} rezervasyon
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        {event.availableCapacity} yer kaldı
                      </Typography>
                    </Stack>
                    <LinearProgress
                      value={occupancy}
                      variant="determinate"
                      aria-label={`Doluluk oranı yüzde ${occupancy}`}
                      sx={{ height: 6, mt: 1 }}
                    />
                  </Box>
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    sx={{
                      bgcolor: 'background.default',
                      borderTop: '1px solid',
                      borderColor: 'divider',
                      gap: 1,
                      p: 2,
                    }}
                  >
                    <ButtonLink to="edit" eventId={event.id}>
                      {cancelled ? 'Kaydı görüntüle' : 'Etkinliği düzenle'}
                    </ButtonLink>
                    <ButtonLink to="attendees" eventId={event.id}>
                      Katılımcılar
                    </ButtonLink>
                    <Button
                      color="error"
                      disabled={cancelled}
                      onClick={() => setEventToCancel(event)}
                      sx={{ ml: { sm: 'auto' } }}
                    >
                      Etkinliği iptal et
                    </Button>
                  </Stack>
                </Surface>
              )
            })}
          </Box>
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
            disabled={!eventsQuery.data?.nextCursor}
            onClick={() =>
              eventsQuery.data?.nextCursor &&
              pager.goForward(eventsQuery.data.nextCursor)
            }
          >
            Sonraki sayfa
          </Button>
        </Stack>
      ) : null}

      <Dialog
        open={Boolean(eventToCancel)}
        onClose={() => !cancelMutation.isPending && setEventToCancel(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>Etkinliği iptal etmek istiyor musunuz?</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            {eventToCancel?.title} yayından kaldırılacak ve yeni rezervasyon
            kabul etmeyecek.
          </Typography>
          {eventToCancel?.reservedCount ? (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {eventToCancel.reservedCount} aktif rezervasyon etkinlik iptali
              nedeniyle kapatılacak. Katılımcılar geçmiş kayıtlarında açıklayıcı
              durumu görecek.
            </Alert>
          ) : null}
          {cancelMutation.isError ? (
            <Box sx={{ mt: 2 }}>
              <ErrorState
                error={cancelMutation.error}
                onRetry={() =>
                  eventToCancel && cancelMutation.mutate(eventToCancel)
                }
              />
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button color="inherit" onClick={() => setEventToCancel(null)}>
            Vazgeç
          </Button>
          <Button
            color="error"
            variant="contained"
            disabled={cancelMutation.isPending}
            onClick={() =>
              eventToCancel && cancelMutation.mutate(eventToCancel)
            }
          >
            {cancelMutation.isPending
              ? 'İptal ediliyor...'
              : 'Etkinliği iptal et'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

function ButtonLink({
  to,
  eventId,
  children,
}: {
  to: 'edit' | 'attendees'
  eventId: string
  children: ReactNode
}) {
  const destination =
    to === 'edit'
      ? '/organizer/events/$eventId/edit'
      : '/organizer/events/$eventId/attendees'
  return (
    <Link
      to={destination}
      params={{ eventId }}
      style={{ textDecoration: 'none' }}
    >
      <Box
        component="span"
        sx={{
          alignItems: 'center',
          borderRadius: 3,
          color: 'primary.light',
          display: 'inline-flex',
          fontSize: '0.875rem',
          fontWeight: 760,
          minHeight: 44,
          px: 1.5,
          '&:hover': { bgcolor: 'action.hover' },
        }}
      >
        {children}
      </Box>
    </Link>
  )
}
