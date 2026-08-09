import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'

import { PublicEventsPage } from '../features/events/PublicEventsPage'
import { RouteNotFoundPage } from '../shared/RouteNotFoundPage'
import { LoginPage, PublicEventDetailPage, RegisterPage } from './lazyPages'
import {
  OrganizerAttendeesRoute,
  OrganizerEventCreateRoute,
  OrganizerEventEditRoute,
  OrganizerEventsRoute,
} from './OrganizerRoutes'
import { RootLayout, UpcomingRoute } from './RouteLayouts'

const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: RouteNotFoundPage,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: PublicEventsPage,
})

const eventDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/events/$eventId',
  component: function EventDetailRoute() {
    const { eventId } = eventDetailRoute.useParams()
    return <PublicEventDetailPage eventId={eventId} />
  },
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: RegisterPage,
})

const upcomingPaths = ['/attendee/reservations'] as const

const upcomingRoutes = upcomingPaths.map((path) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: UpcomingRoute,
  }),
)

const organizerEventsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events',
  component: OrganizerEventsRoute,
})

const organizerCreateRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events/new',
  component: OrganizerEventCreateRoute,
})

const organizerEditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events/$eventId/edit',
  component: function OrganizerEditRoute() {
    const { eventId } = organizerEditRoute.useParams()
    return <OrganizerEventEditRoute eventId={eventId} />
  },
})

const organizerAttendeesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events/$eventId/attendees',
  component: function EventAttendeesRoute() {
    const { eventId } = organizerAttendeesRoute.useParams()
    return <OrganizerAttendeesRoute eventId={eventId} />
  },
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  eventDetailRoute,
  loginRoute,
  registerRoute,
  ...upcomingRoutes,
  organizerEventsRoute,
  organizerCreateRoute,
  organizerEditRoute,
  organizerAttendeesRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
