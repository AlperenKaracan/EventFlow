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

export const OrganizerEventsPage = lazy(async () => ({
  default: (await import('../features/organizer/OrganizerEventsPage'))
    .OrganizerEventsPage,
}))

export const OrganizerEventFormPage = lazy(async () => ({
  default: (await import('../features/organizer/OrganizerEventFormPage'))
    .OrganizerEventFormPage,
}))

export const OrganizerAttendeesPage = lazy(async () => ({
  default: (await import('../features/organizer/OrganizerAttendeesPage'))
    .OrganizerAttendeesPage,
}))
