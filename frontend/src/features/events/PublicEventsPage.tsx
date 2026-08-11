import { useQuery } from '@tanstack/react-query'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { trTR } from '@mui/x-date-pickers/locales'
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import dayjs from 'dayjs'
import 'dayjs/locale/tr'
import { type FormEvent, useState } from 'react'

import {
  fetchPublicCategories,
  fetchPublicEvents,
  type PublicEventFilters,
} from '../../api/publicEvents'
import { designTokens } from '../../app/theme'
import { EmptyState, ErrorState, LoadingState } from '../../shared/AsyncState'
import { PageIntro } from '../../shared/ui/PageIntro'
import { Surface } from '../../shared/ui/Surface'
import { EventCard } from './EventCard'
import { useCursorPager } from './cursorPager'
import { validatePublicEventFilters } from './publicEventFilters'

const emptyFilters: PublicEventFilters = {
  query: '',
  category: '',
  dateFrom: '',
  dateTo: '',
}

export function PublicEventsPage() {
  const pager = useCursorPager()
  const [draftFilters, setDraftFilters] =
    useState<PublicEventFilters>(emptyFilters)
  const [filters, setFilters] = useState<PublicEventFilters>(emptyFilters)
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
    const validationError = validatePublicEventFilters(draftFilters)
    if (validationError) {
      setFilterError(validationError)
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
    setDraftFilters(emptyFilters)
    setFilters(emptyFilters)
    setFilterError(null)
    pager.reset()
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
        eyebrow="ETKİNLİK KEŞFİ"
        title="Takvimine değer katacak etkinliği bul."
        description="Şehrindeki buluşmaları, atölyeleri ve deneyimleri keşfet. Ayrıntıları incele, yerini güvenle ayır."
        actions={
          eventsQuery.data?.items.length ? (
            <Chip
              aria-live="polite"
              label={`${eventsQuery.data.items.length} etkinlik listeleniyor`}
              variant="outlined"
              sx={{ color: 'text.secondary' }}
            />
          ) : null
        }
      />

      <Box
        component="form"
        onSubmit={applyFilters}
        aria-label="Etkinlikleri filtrele"
      >
        <Surface sx={{ mt: { xs: 4, md: 5 }, p: { xs: 2, md: 2.5 } }}>
          <Stack sx={{ gap: 2 }}>
            <Box
              sx={{
                display: 'grid',
                gap: 1.75,
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  lg: 'minmax(280px, 1.5fr) repeat(3, minmax(175px, 1fr))',
                },
              }}
            >
              <TextField
                label="Etkinlik ara"
                placeholder="Başlık, konu veya anahtar kelime"
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
                  trTR.components.MuiLocalizationProvider.defaultProps
                    .localeText
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
                  value={
                    draftFilters.dateTo ? dayjs(draftFilters.dateTo) : null
                  }
                  onChange={(value) =>
                    setDraftFilters((current) => ({
                      ...current,
                      dateTo: value?.isValid()
                        ? value.format('YYYY-MM-DD')
                        : '',
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
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              sx={{ alignItems: { sm: 'center' }, gap: 1.25 }}
            >
              <Button type="submit" variant="contained">
                Sonuçları göster
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
              {hasFilters ? (
                <Typography
                  color="text.secondary"
                  variant="caption"
                  sx={{ ml: { sm: 'auto' } }}
                >
                  Aktif filtreler sonuçlara uygulandı.
                </Typography>
              ) : null}
            </Stack>
          </Stack>
        </Surface>
      </Box>

      <Box
        component="section"
        aria-labelledby="events-heading"
        sx={{ mt: { xs: 4, md: 5 } }}
      >
        <Stack
          direction="row"
          sx={{
            alignItems: 'baseline',
            justifyContent: 'space-between',
            mb: 2.5,
          }}
        >
          <Typography id="events-heading" component="h2" variant="h4">
            Yaklaşan etkinlikler
          </Typography>
          <Typography color="text.secondary" variant="body2">
            Sayfa {pager.page}
          </Typography>
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
            title={
              hasFilters ? 'Eşleşen etkinlik bulunamadı' : 'Henüz etkinlik yok'
            }
            description={
              hasFilters
                ? 'Arama ifadesini veya filtreleri değiştirerek yeniden deneyin.'
                : 'Yeni etkinlikler yayınlandığında burada görünecek.'
            }
            action={
              hasFilters ? (
                <Button onClick={clearFilters}>Tüm etkinlikleri göster</Button>
              ) : undefined
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
            sx={{
              alignItems: 'center',
              gap: 1.5,
              justifyContent: 'center',
              mt: 5,
            }}
          >
            <Button
              variant="outlined"
              disabled={!pager.canGoBack || eventsQuery.isFetching}
              onClick={pager.goBack}
            >
              Önceki sayfa
            </Button>
            <Typography aria-live="polite" color="text.secondary">
              {pager.page}. sayfa
            </Typography>
            <Button
              variant="outlined"
              disabled={!eventsQuery.data.nextCursor || eventsQuery.isFetching}
              onClick={() =>
                eventsQuery.data.nextCursor &&
                pager.goForward(eventsQuery.data.nextCursor)
              }
            >
              Sonraki sayfa
            </Button>
          </Stack>
        ) : null}
      </Box>
    </Container>
  )
}
