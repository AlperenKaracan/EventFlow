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
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 4, md: 7 } }}>
      <Box
        component="section"
        sx={{
          alignItems: { sm: 'end' },
          display: { sm: 'flex' },
          justifyContent: 'space-between',
          mb: { xs: 4, md: 5 },
        }}
      >
        <Box sx={{ maxWidth: 680 }}>
          <Typography
            component="p"
            color="secondary.main"
            sx={{ fontWeight: 800 }}
          >
            EVENTFLOW KEŞİF
          </Typography>
          <Typography component="h1" variant="h2" sx={{ mt: 0.75 }}>
            Yaklaşan etkinlikler
          </Typography>
          <Typography
            sx={{
              color: 'text.secondary',
              fontSize: { xs: '0.98rem', md: '1.08rem' },
              mt: 1.25,
            }}
          >
            İlgi alanına uygun etkinliği bul, ayrıntıları incele ve yerini
            güvenle ayır.
          </Typography>
        </Box>
        {eventsQuery.data?.items.length ? (
          <Typography
            color="text.secondary"
            sx={{ mt: { xs: 2, sm: 0 } }}
            variant="body2"
          >
            Bu sayfada {eventsQuery.data.items.length} etkinlik
          </Typography>
        ) : null}
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
            gap: 2.5,
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
