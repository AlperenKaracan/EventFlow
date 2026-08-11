import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Container,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { trTR } from '@mui/x-date-pickers/locales'
import dayjs from 'dayjs'
import 'dayjs/locale/tr'
import { type FormEvent, useState } from 'react'

import {
  fetchPublicCategories,
  fetchPublicEvents,
  type PublicEventFilters,
} from '../../api/publicEvents'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { EventCard } from './EventCard'
import { useCursorPager } from './cursorPager'

export function PublicEventsPage() {
  const pager = useCursorPager()
  const [draftFilters, setDraftFilters] = useState<PublicEventFilters>({
    query: '',
    category: '',
    dateFrom: '',
    dateTo: '',
  })
  const [filters, setFilters] = useState<PublicEventFilters>(draftFilters)
  const [filterError, setFilterError] = useState<string | null>(null)
  const categoriesQuery = useQuery({
    queryKey: ['public-categories'],
    queryFn: fetchPublicCategories,
    staleTime: 5 * 60 * 1000,
  })
  const eventsQuery = useQuery({
    queryKey: ['public-events', filters, pager.cursor],
    queryFn: () => fetchPublicEvents(pager.cursor, filters),
  })
  const hasFilters = Object.values(filters).some(Boolean)

  const applyFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (
      draftFilters.dateFrom &&
      draftFilters.dateTo &&
      draftFilters.dateFrom > draftFilters.dateTo
    ) {
      setFilterError('Başlangıç tarihi bitiş tarihinden sonra olamaz.')
      return
    }
    setFilterError(null)
    pager.reset()
    setFilters({
      ...draftFilters,
      query: draftFilters.query.trim().replace(/\s+/g, ' '),
    })
  }

  const clearFilters = () => {
    const emptyFilters: PublicEventFilters = {
      query: '',
      category: '',
      dateFrom: '',
      dateTo: '',
    }
    setDraftFilters(emptyFilters)
    setFilters(emptyFilters)
    setFilterError(null)
    pager.reset()
  }

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
            ETKİNLİK KEŞFİ
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
          <Box
            aria-live="polite"
            sx={{
              bgcolor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 999,
              color: 'text.secondary',
              mt: { xs: 2.5, sm: 0 },
              px: 1.75,
              py: 0.85,
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              {eventsQuery.data.items.length} etkinlik listeleniyor
            </Typography>
          </Box>
        ) : null}
      </Box>

      <Paper
        component="form"
        onSubmit={applyFilters}
        aria-label="Etkinlikleri filtrele"
        variant="outlined"
        sx={{ mb: 4, p: { xs: 2, md: 2.5 } }}
      >
        <Stack spacing={2}>
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: {
                xs: '1fr',
                md: 'minmax(240px, 1.5fr) repeat(3, minmax(170px, 1fr))',
              },
            }}
          >
            <TextField
              label="Etkinlik ara"
              placeholder="Başlık veya açıklama"
              value={draftFilters.query}
              onChange={(event) =>
                setDraftFilters((current) => ({
                  ...current,
                  query: event.target.value,
                }))
              }
              slotProps={{ htmlInput: { maxLength: 120 } }}
            />
            <TextField
              select
              label="Kategori"
              value={draftFilters.category}
              disabled={categoriesQuery.isPending}
              onChange={(event) =>
                setDraftFilters((current) => ({
                  ...current,
                  category: event.target.value,
                }))
              }
            >
              <MenuItem value="">Tüm kategoriler</MenuItem>
              {categoriesQuery.data?.map((category) => (
                <MenuItem key={category.id} value={category.slug}>
                  {category.name}
                </MenuItem>
              ))}
            </TextField>
            <LocalizationProvider
              dateAdapter={AdapterDayjs}
              adapterLocale="tr"
              localeText={
                trTR.components.MuiLocalizationProvider.defaultProps.localeText
              }
            >
              <DatePicker
                label="Başlangıç tarihi"
                format="DD.MM.YYYY"
                value={
                  draftFilters.dateFrom ? dayjs(draftFilters.dateFrom) : null
                }
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    dateFrom: value?.isValid()
                      ? value.format('YYYY-MM-DD')
                      : '',
                  }))
                }
              />
              <DatePicker
                label="Bitiş tarihi"
                format="DD.MM.YYYY"
                minDate={
                  draftFilters.dateFrom
                    ? dayjs(draftFilters.dateFrom)
                    : undefined
                }
                value={draftFilters.dateTo ? dayjs(draftFilters.dateTo) : null}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    dateTo: value?.isValid() ? value.format('YYYY-MM-DD') : '',
                  }))
                }
              />
            </LocalizationProvider>
          </Box>
          {filterError ? <Alert severity="error">{filterError}</Alert> : null}
          {categoriesQuery.isError ? (
            <Alert
              severity="warning"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => void categoriesQuery.refetch()}
                >
                  Tekrar dene
                </Button>
              }
            >
              Kategoriler alınamadı. Arama ve tarih filtrelerini kullanmaya
              devam edebilirsiniz.
            </Alert>
          ) : null}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button type="submit" variant="contained">
              Filtreleri uygula
            </Button>
            <Button
              type="button"
              variant="text"
              disabled={
                !hasFilters && !Object.values(draftFilters).some(Boolean)
              }
              onClick={clearFilters}
            >
              Filtreleri temizle
            </Button>
          </Stack>
        </Stack>
      </Paper>

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
          title={
            hasFilters ? 'Eşleşen etkinlik bulunamadı' : 'Henüz etkinlik yok'
          }
          description={
            hasFilters
              ? 'Arama ifadesini veya filtreleri değiştirerek yeniden deneyin.'
              : 'Yeni etkinlikler yayınlandığında burada görünecek.'
          }
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
