import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Avatar,
  Box,
  Button,
  Container,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'

import { fetchEventAttendees, fetchOwnedEvent } from '../../api/organizer'
import { designTokens } from '../../app/theme'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { PageIntro } from '../../shared/ui/PageIntro'
import { StatCard, Surface } from '../../shared/ui/Surface'
import { useCursorPager } from '../events/cursorPager'

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function OrganizerAttendeesPage({ eventId }: { eventId: string }) {
  const pager = useCursorPager()
  const eventQuery = useQuery({
    queryKey: ['owned-event', eventId],
    queryFn: () => fetchOwnedEvent(eventId),
  })
  const attendeesQuery = useQuery({
    queryKey: ['event-attendees', eventId, pager.cursor],
    queryFn: () => fetchEventAttendees(eventId, pager.cursor),
  })

  if (eventQuery.isPending || attendeesQuery.isPending) {
    return (
      <Container maxWidth="lg">
        <LoadingState label="Katılımcılar yükleniyor" />
      </Container>
    )
  }
  const error = eventQuery.error ?? attendeesQuery.error
  if (error) {
    return (
      <Container component="main" maxWidth="md" sx={{ py: 8 }}>
        <ErrorState
          error={error}
          onRetry={() => {
            void eventQuery.refetch()
            void attendeesQuery.refetch()
          }}
        />
      </Container>
    )
  }
  if (!eventQuery.data || !attendeesQuery.data)
    return <LoadingState label="Katılımcılar yükleniyor" />

  const event = eventQuery.data
  const attendees = attendeesQuery.data
  const occupancy = Math.min(
    100,
    Math.round((event.reservedCount / event.capacity) * 100),
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
      <Button
        component={Link}
        to="/organizer/events"
        color="inherit"
        sx={{ color: 'text.secondary', mb: 3 }}
      >
        ← Etkinliklerime dön
      </Button>
      <PageIntro
        eyebrow="KATILIMCI LİSTESİ"
        title={event.title}
        description="Aktif rezervasyonları ve katılımcı iletişim bilgilerini düzenli bir görünümde takip edin."
        actions={
          <Link
            to="/organizer/events/$eventId/edit"
            params={{ eventId }}
            style={{ textDecoration: 'none' }}
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
                minHeight: 44,
                px: 2,
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                },
              }}
            >
              Etkinliği görüntüle
            </Box>
          </Link>
        }
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
          mt: 4,
        }}
      >
        <StatCard
          label="Aktif rezervasyon"
          value={event.reservedCount}
          accent="success.main"
          hint="Onaylı katılımcı"
        />
        <StatCard
          label="Toplam kontenjan"
          value={event.capacity}
          hint="Planlanan kapasite"
        />
        <StatCard
          label="Doluluk"
          value={`%${occupancy}`}
          accent="info.main"
          hint={`${event.availableCapacity} yer kaldı`}
        />
      </Box>

      {attendees.items.length === 0 ? (
        <EmptyState
          title="Henüz katılımcı yok"
          description="Rezervasyon yapan katılımcılar burada görünecek."
        />
      ) : (
        <>
          <TableContainer
            component={Surface}
            sx={{ display: { xs: 'none', md: 'block' }, mt: 4, p: 0 }}
          >
            <Table aria-label={`${event.title} katılımcıları`}>
              <TableHead>
                <TableRow>
                  <TableCell>Katılımcı</TableCell>
                  <TableCell>İletişim</TableCell>
                  <TableCell>Rezervasyon zamanı</TableCell>
                  <TableCell align="right">Durum</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {attendees.items.map((attendee) => (
                  <TableRow key={attendee.reservationId} hover>
                    <TableCell>
                      <Stack
                        direction="row"
                        sx={{ alignItems: 'center', gap: 1.5 }}
                      >
                        <AttendeeAvatar fullName={attendee.fullName} />
                        <Typography variant="body2" sx={{ fontWeight: 760 }}>
                          {attendee.fullName}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography color="text.secondary" variant="body2">
                        {attendee.email}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography color="text.secondary" variant="body2">
                        {dateFormatter.format(new Date(attendee.reservedAt))}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        color="success.main"
                        variant="body2"
                        sx={{ fontWeight: 760 }}
                      >
                        Aktif
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Stack
            aria-label={`${event.title} katılımcıları`}
            sx={{ display: { md: 'none' }, gap: 1.5, mt: 4 }}
          >
            {attendees.items.map((attendee) => (
              <Surface
                component="article"
                key={attendee.reservationId}
                sx={{ p: 2.5 }}
              >
                <Stack direction="row" sx={{ alignItems: 'center', gap: 1.5 }}>
                  <AttendeeAvatar fullName={attendee.fullName} />
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 760 }}>
                      {attendee.fullName}
                    </Typography>
                    <Typography color="text.secondary" noWrap variant="body2">
                      {attendee.email}
                    </Typography>
                  </Box>
                </Stack>
                <Typography
                  color="text.secondary"
                  variant="caption"
                  sx={{ display: 'block', mt: 2 }}
                >
                  Rezervasyon:{' '}
                  {dateFormatter.format(new Date(attendee.reservedAt))}
                </Typography>
              </Surface>
            ))}
          </Stack>
        </>
      )}

      {attendees.items.length ? (
        <Stack
          direction="row"
          sx={{
            alignItems: 'center',
            gap: 1.5,
            justifyContent: 'center',
            mt: 4,
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
            disabled={!attendees.nextCursor}
            onClick={() =>
              attendees.nextCursor && pager.goForward(attendees.nextCursor)
            }
          >
            Sonraki sayfa
          </Button>
        </Stack>
      ) : null}
    </Container>
  )
}

function AttendeeAvatar({ fullName }: { fullName: string }) {
  const initials = fullName
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toLocaleUpperCase('tr-TR'))
    .join('')
  return (
    <Avatar
      aria-hidden="true"
      sx={{
        bgcolor: 'action.selected',
        color: 'primary.light',
        fontSize: 13,
        fontWeight: 850,
        height: 36,
        width: 36,
      }}
    >
      {initials}
    </Avatar>
  )
}
