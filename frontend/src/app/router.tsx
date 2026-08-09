import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'

import { PublicEventDetailPage } from '../features/events/PublicEventDetailPage'
import { PublicEventsPage } from '../features/events/PublicEventsPage'
import { RouteNotFoundPage } from '../shared/RouteNotFoundPage'
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

const upcomingPaths = [
  '/login',
  '/register',
  '/attendee/reservations',
  '/organizer/events',
  '/organizer/events/new',
] as const

const upcomingRoutes = upcomingPaths.map((path) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: UpcomingRoute,
  }),
)

const organizerEditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events/$eventId/edit',
  component: UpcomingRoute,
})

const organizerAttendeesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizer/events/$eventId/attendees',
  component: UpcomingRoute,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  eventDetailRoute,
  ...upcomingRoutes,
  organizerEditRoute,
  organizerAttendeesRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
