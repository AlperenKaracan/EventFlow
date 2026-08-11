import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { beforeEach, vi } from 'vitest'

import { cancelMyReservation, fetchMyReservations } from '../../api/attendee'
import type { ReservationHistoryResponse } from '../../api/generated'
import { ReservationsPage } from './ReservationsPage'

vi.mock('../../api/attendee', () => ({
  cancelMyReservation: vi.fn(),
  createReservationIntent: vi.fn((eventId: string) => ({
    eventId,
    idempotencyKey: 'test-key',
  })),
  fetchMyReservations: vi.fn(),
  reserveEvent: vi.fn(),
}))

const reservation: ReservationHistoryResponse = {
  id: 'reservation-1',
  status: 'ACTIVE',
  createdAt: '2035-05-01T10:00:00Z',
  updatedAt: '2035-05-01T10:00:00Z',
  cancelledAt: null,
  event: {
    id: 'event-1',
    title: 'Tasarım Buluşması',
    location: 'İstanbul',
    startsAt: '2035-05-12T16:00:00Z',
    timezone: 'Europe/Istanbul',
    status: 'ACTIVE',
  },
}

function renderPage() {
  const rootRoute = createRootRoute()
  const pageRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: ReservationsPage,
  })
  const eventRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/events/$eventId',
    component: () => null,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([pageRoute, eventRoute]),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('ReservationsPage', () => {
  beforeEach(() => {
    vi.mocked(fetchMyReservations).mockResolvedValue({
      items: [reservation],
      nextCursor: null,
      hasMore: false,
    })
    vi.mocked(cancelMyReservation).mockResolvedValue()
  })

  it('requires confirmation before cancelling a reservation', async () => {
    renderPage()
    expect(
      await screen.findByRole(
        'heading',
        { name: reservation.event.title },
        { timeout: 5000 },
      ),
    ).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Rezervasyonu iptal et' }),
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(cancelMyReservation).not.toHaveBeenCalled()

    fireEvent.click(
      within(dialog).getByRole('button', { name: 'Rezervasyonu iptal et' }),
    )
    await waitFor(() => expect(cancelMyReservation).toHaveBeenCalled())
    expect(vi.mocked(cancelMyReservation).mock.calls[0]?.[0]).toBe(
      reservation.id,
    )
  })
})
