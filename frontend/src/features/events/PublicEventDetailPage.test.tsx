import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { beforeEach, vi } from 'vitest'

import { ApiError } from '../../api/errors'
import type { PublicEventResponse } from '../../api/generated'
import { fetchPublicEvent } from '../../api/publicEvents'
import { AuthContext } from '../../auth/authContext'
import { PublicEventDetailPage } from './PublicEventDetailPage'

vi.mock('../../api/publicEvents', () => ({ fetchPublicEvent: vi.fn() }))

const event: PublicEventResponse = {
  id: 'event-1',
  category: { id: 'category-1', name: 'Müzik', slug: 'muzik' },
  title: 'Boğaz Konseri',
  description: 'Açık havada canlı müzik.',
  location: 'İstanbul',
  startsAt: '2026-09-10T18:00:00Z',
  timezone: 'Europe/Istanbul',
  capacity: 100,
  reservedCount: 75,
  availableCapacity: 25,
}

function renderDetail() {
  const rootRoute = createRootRoute()
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: () => <PublicEventDetailPage eventId="event-1" />,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute]),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider
        value={{
          session: { status: 'anonymous', user: null },
          login: () => Promise.reject(new Error('not used')),
          logout: () => Promise.resolve(),
          register: () => Promise.reject(new Error('not used')),
        }}
      >
        <RouterProvider router={router} />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('PublicEventDetailPage', () => {
  beforeEach(() => {
    vi.mocked(fetchPublicEvent).mockReset()
  })

  it('renders event details and capacity', async () => {
    vi.mocked(fetchPublicEvent).mockResolvedValue(event)

    renderDetail()

    expect(
      await screen.findByRole('heading', { name: event.title }),
    ).toBeInTheDocument()
    expect(screen.getByText(event.description)).toBeInTheDocument()
    expect(screen.getByText('25 yer kaldı')).toBeInTheDocument()
    expect(fetchPublicEvent).toHaveBeenCalledWith('event-1')
  })

  it('renders the backend request ID on failure', async () => {
    vi.mocked(fetchPublicEvent).mockRejectedValue(
      new ApiError('Etkinlik bulunamadı.', { requestId: 'req-detail-404' }),
    )

    renderDetail()

    expect(await screen.findByText('Etkinlik bulunamadı.')).toBeInTheDocument()
    expect(screen.getByText(/req-detail-404/)).toBeInTheDocument()
  })
})
