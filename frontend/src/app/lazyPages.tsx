import { lazy } from 'react'

export const LoginPage = lazy(async () => ({
  default: (await import('../features/auth/LoginPage')).LoginPage,
}))

export const RegisterPage = lazy(async () => ({
  default: (await import('../features/auth/RegisterPage')).RegisterPage,
}))

export const PublicEventDetailPage = lazy(async () => ({
  default: (await import('../features/events/PublicEventDetailPage'))
    .PublicEventDetailPage,
}))
