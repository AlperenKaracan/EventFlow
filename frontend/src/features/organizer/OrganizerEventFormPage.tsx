import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { trTR } from '@mui/x-date-pickers/locales'
import dayjs from 'dayjs'
import 'dayjs/locale/tr'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { useEffect } from 'react'

import {
  createOwnedEvent,
  fetchCategories,
  fetchOwnedEvent,
  updateOwnedEvent,
} from '../../api/organizer'
import { ApiError } from '../../api/errors'
import { LoadingState } from '../../shared/AsyncState'
import { useFeedback } from '../../shared/feedback'
import {
  localDateTimeToZonedIso,
  zonedIsoToLocalDateTime,
} from '../../shared/timezone'
import {
  eventFormSchema,
  type EventFormInput,
  type EventFormValues,
} from './eventSchema'
import {
  LOCATION_OPTIONS,
  TIMEZONE_OPTIONS,
  timezoneOption,
} from './eventFormOptions'

export function OrganizerEventFormPage({ eventId }: { eventId?: string }) {
  const isEditing = Boolean(eventId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const feedback = useFeedback()
  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
  })
  const eventQuery = useQuery({
    queryKey: ['owned-event', eventId],
    queryFn: () => fetchOwnedEvent(eventId!),
    enabled: isEditing,
  })
  const form = useForm<EventFormInput, unknown, EventFormValues>({
    resolver: zodResolver(eventFormSchema),
    defaultValues: {
      categoryId: '',
      title: '',
      description: '',
      location: '',
      startsAt: '',
      timezone:
        Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Istanbul',
      capacity: 1,
    },
  })
  const title = useWatch({ control: form.control, name: 'title' })
  const isCancelled = eventQuery.data?.status === 'CANCELLED'

  useEffect(() => {
    if (!eventQuery.data) return
    form.reset({
      categoryId: eventQuery.data.category.id,
      title: eventQuery.data.title,
      description: eventQuery.data.description,
      location: eventQuery.data.location,
      startsAt: zonedIsoToLocalDateTime(
        eventQuery.data.startsAt,
        eventQuery.data.timezone,
      ),
      timezone: eventQuery.data.timezone,
      capacity: eventQuery.data.capacity,
    })
  }, [eventQuery.data, form])

  const mutation = useMutation({
    mutationFn: async (values: EventFormValues) => {
      if (isCancelled) {
        throw new ApiError('İptal edilen etkinlikler düzenlenemez.', {
          code: 'EVENT_CANCELLED',
        })
      }
      const payload = {
        ...values,
        startsAt: localDateTimeToZonedIso(values.startsAt, values.timezone),
      }
      if (eventId && eventQuery.data) {
        return updateOwnedEvent(eventId, {
          ...payload,
          expectedVersion: eventQuery.data.version,
        })
      }
      return createOwnedEvent(payload)
    },
    onSuccess: async (event) => {
      await queryClient.invalidateQueries({ queryKey: ['owned-events'] })
      queryClient.setQueryData(['owned-event', event.id], event)
      if (isEditing) {
        feedback.showSuccess('Değişiklikler kaydedildi.')
        return
      }
      feedback.showSuccess(
        'Etkinlik oluşturuldu. Etkinliklerim sayfasına yönlendirildiniz.',
      )
      await navigate({ to: '/organizer/events' })
    },
  })

  const submit = form.handleSubmit((values) =>
    mutation.mutateAsync(values).then(() => undefined),
  )
  const mutationError =
    mutation.error instanceof ApiError ? mutation.error : null
  const hasVersionConflict = mutationError?.code === 'EVENT_VERSION_CONFLICT'

  const reloadCurrentEvent = async () => {
    mutation.reset()
    await eventQuery.refetch()
  }

  if (categoriesQuery.isPending || (isEditing && eventQuery.isPending)) {
    return <LoadingState label="Etkinlik formu yükleniyor" />
  }

  const loadError = categoriesQuery.error ?? eventQuery.error
  if (loadError) {
    return (
      <Container component="main" maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error">
          {loadError instanceof ApiError
            ? loadError.message
            : 'Form yüklenemedi.'}
        </Alert>
      </Container>
    )
  }

  return (
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 3, md: 6 } }}>
      <Button
        onClick={() => void navigate({ to: '/organizer/events' })}
        sx={{ mb: 2, px: 0 }}
      >
        ← Etkinliklerime dön
      </Button>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        sx={{ alignItems: { md: 'flex-end' }, gap: 2, mb: 4 }}
      >
        <Box sx={{ flex: 1 }}>
          <Typography
            component="p"
            color="primary"
            sx={{ fontWeight: 800, letterSpacing: '0.08em' }}
          >
            ORGANİZATÖR STÜDYOSU
          </Typography>
          <Typography component="h1" variant="h2" sx={{ mt: 0.75 }}>
            {isCancelled
              ? 'İptal edilen etkinlik'
              : isEditing
                ? 'Etkinliği düzenle'
                : 'Yeni bir deneyim oluştur'}
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 680 }}>
            {isCancelled
              ? 'Bu etkinliğin son yayınlanan bilgilerini inceleyebilirsiniz.'
              : 'Katılımcıların karar vermesi için ihtiyaç duyduğu tüm bilgileri tek bir yerde, anlaşılır biçimde paylaşın.'}
          </Typography>
        </Box>
        {isEditing && eventQuery.data && isCancelled ? (
          <Stack direction="row" sx={{ alignItems: 'center', gap: 1.5 }}>
            <Chip label="İptal edildi" color="default" size="small" />
          </Stack>
        ) : null}
      </Stack>
      {isCancelled ? (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Bu etkinlik organizatör tarafından iptal edildi. Yeni rezervasyon
          kabul etmez ve bilgileri artık değiştirilemez.
        </Alert>
      ) : null}
      <Paper
        component="form"
        onSubmit={(event) => void submit(event)}
        noValidate
        variant="outlined"
        sx={{ overflow: 'hidden' }}
      >
        <Box sx={{ p: { xs: 2.5, sm: 4 } }}>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 800 }}>
            Temel bilgiler
          </Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>
            Net bir başlık ve kısa açıklama etkinliğinizi öne çıkarır.
          </Typography>
          {mutation.isError && !hasVersionConflict ? (
            <Alert severity="error" sx={{ mt: 3 }}>
              {mutationError?.message ?? 'Etkinlik kaydedilemedi.'}
            </Alert>
          ) : null}
          <Box
            sx={{
              display: 'grid',
              gap: 2.5,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(12, 1fr)' },
              mt: 3,
            }}
          >
            <Controller
              control={form.control}
              name="categoryId"
              render={({ field }) => (
                <TextField
                  select
                  disabled={isCancelled}
                  fullWidth
                  label="Kategori"
                  error={Boolean(form.formState.errors.categoryId)}
                  helperText={
                    form.formState.errors.categoryId?.message ??
                    'Etkinliğin en uygun kategorisini seçin.'
                  }
                  sx={{ gridColumn: { md: 'span 5' } }}
                  {...field}
                >
                  {categoriesQuery.data?.map((category) => (
                    <MenuItem value={category.id} key={category.id}>
                      {category.name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <TextField
              fullWidth
              disabled={isCancelled}
              label="Başlık"
              placeholder="Örn. İstanbul Ürün Tasarımı Buluşması"
              error={Boolean(form.formState.errors.title)}
              helperText={
                form.formState.errors.title?.message ??
                `${title.length}/160 karakter`
              }
              sx={{ gridColumn: { md: 'span 7' } }}
              {...form.register('title')}
            />
            <TextField
              fullWidth
              disabled={isCancelled}
              label="Açıklama"
              placeholder="Katılımcıları nelerin beklediğini, programı ve önemli detayları anlatın."
              multiline
              minRows={5}
              error={Boolean(form.formState.errors.description)}
              helperText={form.formState.errors.description?.message}
              sx={{ gridColumn: { md: 'span 12' } }}
              {...form.register('description')}
            />
          </Box>
        </Box>
        <Divider />
        <Box sx={{ p: { xs: 2.5, sm: 4 } }}>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 800 }}>
            Zaman ve yer
          </Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>
            Tarih, saat ve saat dilimi birlikte değerlendirilir.
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gap: 2.5,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
              mt: 3,
            }}
          >
            <Controller
              control={form.control}
              name="location"
              render={({ field }) => (
                <Autocomplete
                  disabled={isCancelled}
                  freeSolo
                  autoHighlight
                  options={[...LOCATION_OPTIONS]}
                  value={field.value || null}
                  onChange={(_, value) => field.onChange(value ?? '')}
                  onInputChange={(_, value) => field.onChange(value)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Konum veya platform"
                      placeholder="Şehir, mekân veya çevrim içi"
                      error={Boolean(form.formState.errors.location)}
                      helperText={
                        form.formState.errors.location?.message ??
                        'Listeden seçebilir veya özel bir mekân yazabilirsiniz.'
                      }
                    />
                  )}
                />
              )}
            />
            <Controller
              control={form.control}
              name="timezone"
              render={({ field }) => (
                <Autocomplete
                  disabled={isCancelled}
                  autoHighlight
                  options={[...TIMEZONE_OPTIONS]}
                  value={timezoneOption(field.value)}
                  onChange={(_, value) => field.onChange(value?.value ?? '')}
                  isOptionEqualToValue={(option, value) =>
                    option.value === value.value
                  }
                  getOptionLabel={(option) => option.label}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Saat dilimi"
                      error={Boolean(form.formState.errors.timezone)}
                      helperText={
                        form.formState.errors.timezone?.message ??
                        'Etkinliğin gerçekleşeceği bölgeyi seçin.'
                      }
                    />
                  )}
                />
              )}
            />
            <Controller
              control={form.control}
              name="startsAt"
              render={({ field }) => (
                <LocalizationProvider
                  dateAdapter={AdapterDayjs}
                  adapterLocale="tr"
                  localeText={
                    trTR.components.MuiLocalizationProvider.defaultProps
                      .localeText
                  }
                >
                  <DateTimePicker
                    disabled={isCancelled}
                    label="Başlangıç tarihi ve saati"
                    ampm={false}
                    format="DD.MM.YYYY HH:mm"
                    minutesStep={5}
                    disablePast={!isEditing}
                    value={field.value ? dayjs(field.value) : null}
                    onChange={(value) =>
                      field.onChange(
                        value?.isValid()
                          ? value.format('YYYY-MM-DDTHH:mm')
                          : '',
                      )
                    }
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(form.formState.errors.startsAt),
                        helperText:
                          form.formState.errors.startsAt?.message ??
                          'Takvimden gün ve saati birlikte seçin.',
                      },
                    }}
                  />
                </LocalizationProvider>
              )}
            />
            <TextField
              fullWidth
              disabled={isCancelled}
              label="Kontenjan"
              type="number"
              slotProps={{ htmlInput: { min: 1 } }}
              error={Boolean(form.formState.errors.capacity)}
              helperText={
                form.formState.errors.capacity?.message ??
                'Katılabilecek toplam kişi sayısı.'
              }
              {...form.register('capacity')}
            />
          </Box>
        </Box>
        <Divider />
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          sx={{
            alignItems: { sm: 'center' },
            bgcolor: 'background.default',
            gap: 2,
            justifyContent: 'space-between',
            p: { xs: 2.5, sm: 3 },
          }}
        >
          <Typography
            aria-live="polite"
            color={form.formState.isDirty ? 'warning.main' : 'text.secondary'}
            variant="body2"
            sx={{ fontWeight: 700 }}
          >
            {isCancelled
              ? 'İptal edilen etkinlik bilgileri salt okunurdur.'
              : form.formState.isDirty
                ? 'Kaydedilmemiş değişiklikleriniz var.'
                : isEditing
                  ? 'Tüm değişiklikler kaydedildi.'
                  : 'Formu doldurarak etkinliğinizi yayınlayın.'}
          </Typography>
          <Stack direction="row" sx={{ gap: 1.5, justifyContent: 'flex-end' }}>
            <Button onClick={() => void navigate({ to: '/organizer/events' })}>
              {isCancelled ? 'Etkinliklerime dön' : 'Vazgeç'}
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={mutation.isPending || isCancelled}
            >
              {isCancelled
                ? 'İptal edildi'
                : mutation.isPending
                  ? 'Kaydediliyor…'
                  : 'Kaydet'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
      <Dialog open={hasVersionConflict} onClose={() => mutation.reset()}>
        <DialogTitle>Etkinlik başka bir yerde güncellendi</DialogTitle>
        <DialogContent>
          <Typography>
            Kaydınız uygulanmadı. Güncel veriyi yükleyerek değişiklikleri
            yeniden değerlendirin.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => mutation.reset()}>Düzenlemeye dön</Button>
          <Button variant="contained" onClick={() => void reloadCurrentEvent()}>
            Güncel veriyi yükle
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
