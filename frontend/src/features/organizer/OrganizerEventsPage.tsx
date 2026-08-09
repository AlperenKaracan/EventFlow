import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from '@mui/material'
import { useState } from 'react'

import { cancelOwnedEvent, fetchOwnedEvents } from '../../api/organizer'
import type { OwnerEventResponse } from '../../api/generated'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
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

  return (
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 4, md: 7 } }}>
      <Stack
        direction="row"
        sx={{ alignItems: 'center', gap: 2, justifyContent: 'space-between' }}
      >
        <Box>
          <Typography component="h1" variant="h2">
            Etkinliklerim
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            Yayınlarınızı, kontenjanı ve katılımcıları yönetin.
          </Typography>
        </Box>
        <Button component={Link} to="/organizer/events/new" variant="contained">
          Yeni etkinlik
        </Button>
      </Stack>

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
          description="İlk etkinliğinizi oluşturarak başlayın."
        />
      ) : null}
      {eventsQuery.data?.items.length ? (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
            mt: 4,
          }}
        >
          {eventsQuery.data.items.map((event) => (
            <Card key={event.id} variant="outlined">
              <CardContent>
                <Stack
                  direction="row"
                  sx={{ gap: 1, justifyContent: 'space-between' }}
                >
                  <Chip
                    label={event.status === 'ACTIVE' ? 'Aktif' : 'İptal edildi'}
                    color={event.status === 'ACTIVE' ? 'success' : 'default'}
                    size="small"
                  />
                  <Typography variant="caption">
                    Sürüm {event.version}
                  </Typography>
                </Stack>
                <Typography
                  component="h2"
                  variant="h6"
                  sx={{ fontWeight: 800, mt: 2 }}
                >
                  {event.title}
                </Typography>
                <Typography color="text.secondary">
                  {event.reservedCount} / {event.capacity} rezervasyon
                </Typography>
              </CardContent>
              <CardActions sx={{ flexWrap: 'wrap' }}>
                <Link
                  to="/organizer/events/$eventId/edit"
                  params={{ eventId: event.id }}
                >
                  <Button component="span">Düzenle</Button>
                </Link>
                <Link
                  to="/organizer/events/$eventId/attendees"
                  params={{ eventId: event.id }}
                >
                  <Button component="span">Katılımcılar</Button>
                </Link>
                <Button
                  color="error"
                  disabled={event.status !== 'ACTIVE'}
                  onClick={() => setEventToCancel(event)}
                >
                  İptal et
                </Button>
              </CardActions>
            </Card>
          ))}
        </Box>
      ) : null}

      {eventsQuery.data?.items.length ? (
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
            disabled={!eventsQuery.data.nextCursor}
            onClick={() =>
              eventsQuery.data.nextCursor &&
              pager.goForward(eventsQuery.data.nextCursor)
            }
          >
            Sonraki
          </Button>
        </Stack>
      ) : null}

      <Dialog
        open={Boolean(eventToCancel)}
        onClose={() => setEventToCancel(null)}
      >
        <DialogTitle>Etkinliği iptal et</DialogTitle>
        <DialogContent>
          <Typography>
            “{eventToCancel?.title}” etkinliği iptal edilecek. Bu işlem yeni
            rezervasyonları durdurur.
          </Typography>
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
          <Button onClick={() => setEventToCancel(null)}>Vazgeç</Button>
          <Button
            color="error"
            variant="contained"
            disabled={cancelMutation.isPending}
            onClick={() =>
              eventToCancel && cancelMutation.mutate(eventToCancel)
            }
          >
            İptal et
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
