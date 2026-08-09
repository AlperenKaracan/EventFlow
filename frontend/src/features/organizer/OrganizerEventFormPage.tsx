import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import {
  Alert,
  Button,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { Controller, useForm } from 'react-hook-form'
import { useEffect } from 'react'

import {
  createOwnedEvent,
  fetchCategories,
  fetchOwnedEvent,
  updateOwnedEvent,
} from '../../api/organizer'
import { ApiError } from '../../api/errors'
import { LoadingState } from '../../shared/AsyncState'
import {
  localDateTimeToZonedIso,
  zonedIsoToLocalDateTime,
} from '../../shared/timezone'
import {
  eventFormSchema,
  type EventFormInput,
  type EventFormValues,
} from './eventSchema'

export function OrganizerEventFormPage({ eventId }: { eventId?: string }) {
  const isEditing = Boolean(eventId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
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
      await navigate({
        to: '/organizer/events/$eventId/edit',
        params: { eventId: event.id },
      })
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
    <Container component="main" maxWidth="md" sx={{ py: { xs: 4, md: 7 } }}>
      <Typography component="h1" variant="h2">
        {isEditing ? 'Etkinliği düzenle' : 'Yeni etkinlik'}
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>
        Zaman, konum ve kontenjan bilgilerini eksiksiz girin.
      </Typography>
      <Stack
        component="form"
        onSubmit={(event) => void submit(event)}
        noValidate
        sx={{ gap: 2 }}
      >
        {mutation.isError && !hasVersionConflict ? (
          <Alert severity="error">
            {mutationError?.message ?? 'Etkinlik kaydedilemedi.'}
            {mutationError?.requestId ? (
              <Typography variant="caption" component="p" sx={{ mt: 1 }}>
                İstek kimliği: <code>{mutationError.requestId}</code>
              </Typography>
            ) : null}
          </Alert>
        ) : null}
        <Controller
          control={form.control}
          name="categoryId"
          render={({ field }) => (
            <TextField
              select
              label="Kategori"
              error={Boolean(form.formState.errors.categoryId)}
              helperText={form.formState.errors.categoryId?.message}
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
          label="Başlık"
          error={Boolean(form.formState.errors.title)}
          helperText={form.formState.errors.title?.message}
          {...form.register('title')}
        />
        <TextField
          label="Açıklama"
          multiline
          minRows={4}
          error={Boolean(form.formState.errors.description)}
          helperText={form.formState.errors.description?.message}
          {...form.register('description')}
        />
        <TextField
          label="Konum"
          error={Boolean(form.formState.errors.location)}
          helperText={form.formState.errors.location?.message}
          {...form.register('location')}
        />
        <TextField
          label="Başlangıç"
          type="datetime-local"
          slotProps={{ inputLabel: { shrink: true } }}
          error={Boolean(form.formState.errors.startsAt)}
          helperText={form.formState.errors.startsAt?.message}
          {...form.register('startsAt')}
        />
        <TextField
          label="IANA saat dilimi"
          error={Boolean(form.formState.errors.timezone)}
          helperText={form.formState.errors.timezone?.message}
          {...form.register('timezone')}
        />
        <TextField
          label="Kapasite"
          type="number"
          slotProps={{ htmlInput: { min: 1 } }}
          error={Boolean(form.formState.errors.capacity)}
          helperText={form.formState.errors.capacity?.message}
          {...form.register('capacity')}
        />
        <Stack direction="row" sx={{ gap: 2, justifyContent: 'flex-end' }}>
          <Button onClick={() => void navigate({ to: '/organizer/events' })}>
            Vazgeç
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Kaydediliyor…' : 'Kaydet'}
          </Button>
        </Stack>
      </Stack>
      <Dialog open={hasVersionConflict} onClose={() => mutation.reset()}>
        <DialogTitle>Etkinlik başka bir yerde güncellendi</DialogTitle>
        <DialogContent>
          <Typography>
            Kaydınız uygulanmadı. Güncel veriyi yükleyerek değişiklikleri
            yeniden değerlendirin.
          </Typography>
          {mutationError?.requestId ? (
            <Typography variant="caption" component="p" sx={{ mt: 2 }}>
              İstek kimliği: <code>{mutationError.requestId}</code>
            </Typography>
          ) : null}
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
