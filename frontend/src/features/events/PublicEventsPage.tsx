import { useQuery } from '@tanstack/react-query'
import { Box, Button, Container, Stack, Typography } from '@mui/material'

import { fetchPublicEvents } from '../../api/publicEvents'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { EventCard } from './EventCard'
import { useCursorPager } from './cursorPager'

export function PublicEventsPage() {
  const pager = useCursorPager()
  const eventsQuery = useQuery({
    queryKey: ['public-events', pager.cursor],
    queryFn: () => fetchPublicEvents(pager.cursor),
  })

  return (
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 5, md: 8 } }}>
      <Box sx={{ maxWidth: 720, mb: 5 }}>
        <Typography component="p" color="primary" sx={{ fontWeight: 800 }}>
          Şehrinde yeni deneyimler keşfet
        </Typography>
        <Typography component="h1" variant="h1" sx={{ mt: 1 }}>
          Yaklaşan etkinlikler
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 2, fontSize: '1.1rem' }}>
          Yerini ayır, planını kolayca yönet ve etkinlik günü geldiğinde
          yalnızca anın tadını çıkar.
        </Typography>
      </Box>

      {eventsQuery.isPending ? (
        <LoadingState label="Etkinlikler yükleniyor" />
      ) : null}
      {eventsQuery.isError ? (
        <ErrorState
          error={eventsQuery.error}
          onRetry={() => void eventsQuery.refetch()}
        />
      ) : null}
      {eventsQuery.data?.items.length === 0 ? (
        <EmptyState
          title="Henüz etkinlik yok"
          description="Yeni etkinlikler yayınlandığında burada görünecek."
        />
      ) : null}
      {eventsQuery.data?.items.length ? (
        <Box
          aria-label="Etkinlik listesi"
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              lg: 'repeat(3, 1fr)',
            },
          }}
        >
          {eventsQuery.data.items.map((event) => (
            <EventCard event={event} key={event.id} />
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
            disabled={!pager.canGoBack || eventsQuery.isFetching}
            onClick={pager.goBack}
          >
            Önceki
          </Button>
          <Typography aria-live="polite">Sayfa {pager.page}</Typography>
          <Button
            variant="outlined"
            disabled={!eventsQuery.data.nextCursor || eventsQuery.isFetching}
            onClick={() => {
              if (eventsQuery.data.nextCursor)
                pager.goForward(eventsQuery.data.nextCursor)
            }}
          >
            Sonraki
          </Button>
        </Stack>
      ) : null}
    </Container>
  )
}
