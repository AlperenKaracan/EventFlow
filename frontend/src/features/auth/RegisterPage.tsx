import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import { Alert, Button, MenuItem, Stack, TextField } from '@mui/material'
import { Controller, useForm } from 'react-hook-form'

import { ApiError } from '../../api/errors'
import { useAuth } from '../../auth/authContext'
import { AuthFormLayout } from './AuthFormLayout'
import { registerSchema, type RegisterFormValues } from './schemas'

export function RegisterPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { fullName: '', email: '', password: '', role: 'attendee' },
  })

  const submit = form.handleSubmit(async (values) => {
    try {
      const user = await auth.register(values)
      await navigate({
        to: user.role === 'organizer' ? '/organizer/events' : '/',
      })
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : 'Kayıt tamamlanamadı.'
      form.setError('root', { message })
    }
  })

  return (
    <AuthFormLayout
      title="EventFlow’a katılın"
      description="Katılımcı olarak yer ayırın veya organizatör olarak etkinliklerinizi yayınlayın."
      footer="register"
    >
      <Stack
        component="form"
        onSubmit={(event) => void submit(event)}
        noValidate
        sx={{ gap: 2 }}
      >
        {form.formState.errors.root?.message ? (
          <Alert severity="error">{form.formState.errors.root.message}</Alert>
        ) : null}
        <TextField
          label="Ad soyad"
          autoComplete="name"
          error={Boolean(form.formState.errors.fullName)}
          helperText={form.formState.errors.fullName?.message}
          {...form.register('fullName')}
        />
        <TextField
          label="E-posta"
          type="email"
          autoComplete="email"
          error={Boolean(form.formState.errors.email)}
          helperText={form.formState.errors.email?.message}
          {...form.register('email')}
        />
        <TextField
          label="Şifre"
          type="password"
          autoComplete="new-password"
          error={Boolean(form.formState.errors.password)}
          helperText={
            form.formState.errors.password?.message ??
            'En az 12 karakter kullanın.'
          }
          {...form.register('password')}
        />
        <Controller
          control={form.control}
          name="role"
          render={({ field }) => (
            <TextField select label="Hesap türü" {...field}>
              <MenuItem value="attendee">Katılımcı</MenuItem>
              <MenuItem value="organizer">Organizatör</MenuItem>
            </TextField>
          )}
        />
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting
            ? 'Hesap oluşturuluyor…'
            : 'Hesap oluştur'}
        </Button>
      </Stack>
    </AuthFormLayout>
  )
}
