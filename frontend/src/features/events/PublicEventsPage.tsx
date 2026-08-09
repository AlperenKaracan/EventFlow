import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Button,
  Chip,
  Container,
  Paper,
  Stack,
  Typography,
} from '@mui/material'

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
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 3, md: 6 } }}>
      <Paper
        component="section"
        variant="outlined"
        sx={{
          background:
            'linear-gradient(135deg, rgba(79,70,229,0.98), rgba(49,46,129,0.96) 52%, rgba(15,118,110,0.94))',
          border: 0,
          borderRadius: { xs: 3, md: 5 },
          color: 'common.white',
          mb: { xs: 4, md: 6 },
          overflow: 'hidden',
          p: { xs: 3, sm: 5, md: 7 },
          position: 'relative',
          '&::after': {
            background:
              'radial-gradient(circle, rgba(255,255,255,.24) 1px, transparent 1px)',
            backgroundSize: '22px 22px',
            content: '""',
            inset: 0,
            maskImage: 'linear-gradient(to left, black, transparent 70%)',
            opacity: 0.5,
            pointerEvents: 'none',
            position: 'absolute',
          },
        }}
      >
        <Box sx={{ maxWidth: 760, position: 'relative', zIndex: 1 }}>
          <Chip
            label="Canlı etkinlik kataloğu"
            sx={{
              bgcolor: 'rgba(255,255,255,.14)',
              color: 'common.white',
              mb: 2.5,
            }}
          />
          <Typography component="h1" variant="h1">
            Yeni insanlarla tanış, yeni deneyimler keşfet.
          </Typography>
          <Typography
            sx={{
              color: 'rgba(255,255,255,.82)',
              fontSize: { xs: '1rem', md: '1.18rem' },
              mt: 2.5,
              maxWidth: 650,
            }}
          >
            Yerini güvenle ayır, planını kolayca yönet ve etkinlik günü
            geldiğinde yalnızca anın tadını çıkar.
          </Typography>
        </Box>
      </Paper>

      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        sx={{
          alignItems: { sm: 'end' },
          gap: 1,
          justifyContent: 'space-between',
          mb: 3,
        }}
      >
        <Box>
          <Typography component="p" color="primary" sx={{ fontWeight: 800 }}>
            KEŞFET
          </Typography>
          <Typography component="h2" variant="h2" sx={{ mt: 0.5 }}>
            Yaklaşan etkinlikler
          </Typography>
        </Box>
        {eventsQuery.data?.items.length ? (
          <Typography color="text.secondary" variant="body2">
            Bu sayfada {eventsQuery.data.items.length} etkinlik
          </Typography>
        ) : null}
      </Stack>

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
