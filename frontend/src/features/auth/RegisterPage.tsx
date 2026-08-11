import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import {
  Alert,
  Box,
  Button,
  FormControl,
  FormControlLabel,
  FormLabel,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
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
      title="EventFlow'a katılın"
      description="Etkinlikleri keşfetmek veya kendi topluluğunuzu büyütmek için hesabınızı oluşturun."
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
        <FormControl>
          <FormLabel id="account-role-label">Hesap türü</FormLabel>
          <Controller
            control={form.control}
            name="role"
            render={({ field }) => (
              <RadioGroup aria-labelledby="account-role-label" {...field}>
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  sx={{ gap: 1.25, mt: 1 }}
                >
                  {[
                    {
                      value: 'attendee',
                      label: 'Katılımcı',
                      hint: 'Etkinlik keşfet ve yer ayır',
                    },
                    {
                      value: 'organizer',
                      label: 'Organizatör',
                      hint: 'Etkinlik oluştur ve yönet',
                    },
                  ].map((option) => (
                    <Box
                      key={option.value}
                      sx={{
                        bgcolor:
                          field.value === option.value
                            ? 'action.selected'
                            : 'background.default',
                        border: '1px solid',
                        borderColor:
                          field.value === option.value
                            ? 'primary.main'
                            : 'divider',
                        borderRadius: 3,
                        flex: 1,
                        p: 1,
                      }}
                    >
                      <FormControlLabel
                        value={option.value}
                        control={<Radio />}
                        label={
                          <Box>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 760 }}
                            >
                              {option.label}
                            </Typography>
                            <Typography
                              color="text.secondary"
                              variant="caption"
                            >
                              {option.hint}
                            </Typography>
                          </Box>
                        }
                        sx={{ alignItems: 'center', m: 0, width: '100%' }}
                      />
                    </Box>
                  ))}
                </Stack>
              </RadioGroup>
            )}
          />
        </FormControl>
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting
            ? 'Hesap oluşturuluyor...'
            : 'Hesap oluştur'}
        </Button>
      </Stack>
    </AuthFormLayout>
  )
}
