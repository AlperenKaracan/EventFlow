import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import { Alert, Button, Stack, TextField } from '@mui/material'
import { useForm } from 'react-hook-form'

import { ApiError } from '../../api/errors'
import { useAuth } from '../../auth/authContext'
import { AuthFormLayout } from './AuthFormLayout'
import { loginSchema, type LoginFormValues } from './schemas'

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const submit = form.handleSubmit(async (values) => {
    try {
      const user = await auth.login(values)
      await navigate({
        to: user.role === 'organizer' ? '/organizer/events' : '/',
      })
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : 'Giriş yapılamadı.'
      form.setError('root', { message })
    }
  })

  return (
    <AuthFormLayout
      title="Tekrar hoş geldiniz"
      description="Rezervasyonlarınızı ve etkinliklerinizi yönetmek için giriş yapın."
      footer="login"
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
          autoComplete="current-password"
          error={Boolean(form.formState.errors.password)}
          helperText={form.formState.errors.password?.message}
          {...form.register('password')}
        />
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? 'Giriş yapılıyor…' : 'Giriş yap'}
        </Button>
      </Stack>
    </AuthFormLayout>
  )
}
