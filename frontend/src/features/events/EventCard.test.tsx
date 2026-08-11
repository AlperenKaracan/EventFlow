import { render, screen } from '@testing-library/react'
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'

import type { PublicEventResponse } from '../../api/generated'
import { EventCard } from './EventCard'

const event: PublicEventResponse = {
  id: 'event-1',
  category: { id: 'category-1', name: 'Teknoloji', slug: 'teknoloji' },
  title: 'TypeScript Buluşması',
  description: 'Tip güvenliği üzerine bir etkinlik.',
  location: 'İstanbul',
  startsAt: '2026-09-10T18:00:00Z',
  timezone: 'Europe/Istanbul',
  capacity: 100,
  reservedCount: 20,
  availableCapacity: 80,
}

function renderCard() {
  const rootRoute = createRootRoute()
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: () => <EventCard event={event} />,
  })
  const detailRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/events/$eventId',
    component: () => null,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute, detailRoute]),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })

  return render(<RouterProvider router={router} />)
}

describe('EventCard', () => {
  it('uses a level-two heading and one semantic detail link', async () => {
    renderCard()

    expect(
      await screen.findByRole('heading', { level: 2, name: event.title }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Etkinliği incele' }),
    ).toHaveAttribute('href', '/events/event-1')
    expect(
      screen.queryByRole('button', { name: 'Etkinliği incele' }),
    ).not.toBeInTheDocument()
  })

  it('presents Turkish date, location, and capacity', async () => {
    renderCard()

    expect(await screen.findByText(/10 Eylül/)).toBeInTheDocument()
    expect(screen.getByText('İstanbul')).toBeInTheDocument()
    expect(screen.getByText('80 yer kaldı')).toBeInTheDocument()
    expect(
      screen.getByRole('progressbar', {
        name: 'Kontenjanın yüzde 20 kadarı dolu',
      }),
    ).toBeInTheDocument()
  })
})
