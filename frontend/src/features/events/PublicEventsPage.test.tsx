import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { type ReactNode } from 'react'
import { beforeEach, vi } from 'vitest'

import { ApiError } from '../../api/errors'
import type { PublicEventResponse } from '../../api/generated'
import {
  fetchPublicCategories,
  fetchPublicEvents,
  type PublicEventFilters,
} from '../../api/publicEvents'
import { PublicEventsPage } from './PublicEventsPage'

vi.mock('../../api/publicEvents', () => ({
  fetchPublicCategories: vi.fn(),
  fetchPublicEvents: vi.fn(),
}))
vi.mock('./EventCard', () => ({
  EventCard: ({ event }: { event: PublicEventResponse }) => (
    <article>{event.title}</article>
  ),
}))

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

const emptyFilters: PublicEventFilters = {
  query: '',
  category: '',
  dateFrom: '',
  dateTo: '',
}

function renderWithQueryClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>,
  )
}

describe('PublicEventsPage', () => {
  beforeEach(() => {
    vi.mocked(fetchPublicEvents).mockReset()
    vi.mocked(fetchPublicCategories).mockReset()
    vi.mocked(fetchPublicCategories).mockResolvedValue([
      { id: 'category-1', name: 'Teknoloji', slug: 'teknoloji' },
    ])
  })

  it('keeps cursor history for forward and backward navigation', async () => {
    vi.mocked(fetchPublicEvents).mockImplementation((cursor) =>
      Promise.resolve({
        items: [
          {
            ...event,
            id: cursor ?? 'first',
            title: cursor ? 'İkinci sayfa' : 'İlk sayfa',
          },
        ],
        nextCursor: cursor ? null : 'cursor-2',
        hasMore: cursor === null,
      }),
    )

    renderWithQueryClient(<PublicEventsPage />)

    expect(
      screen.getByRole('heading', { name: 'Yaklaşan etkinlikler' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Yeni insanlarla tanış, yeni deneyimler keşfet.'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('ETKİNLİK KEŞFİ')).toBeInTheDocument()
    expect(await screen.findByText('İlk sayfa')).toBeInTheDocument()
    expect(screen.getByText('1 etkinlik listeleniyor')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sonraki' }))

    expect(await screen.findByText('İkinci sayfa')).toBeInTheDocument()
    expect(screen.getByText('Sayfa 2')).toBeInTheDocument()
    expect(fetchPublicEvents).toHaveBeenLastCalledWith('cursor-2', emptyFilters)

    fireEvent.click(screen.getByRole('button', { name: 'Önceki' }))
    expect(await screen.findByText('İlk sayfa')).toBeInTheDocument()
    expect(screen.getByText('Sayfa 1')).toBeInTheDocument()
  })

  it('applies search filters and resets cursor history', async () => {
    vi.mocked(fetchPublicEvents).mockImplementation((cursor, filters) =>
      Promise.resolve({
        items: [{ ...event, title: filters.query || 'İlk sayfa' }],
        nextCursor: cursor ? null : 'cursor-2',
        hasMore: cursor === null,
      }),
    )

    renderWithQueryClient(<PublicEventsPage />)

    await screen.findByText('İlk sayfa')
    fireEvent.click(screen.getByRole('button', { name: 'Sonraki' }))
    await screen.findByText('Sayfa 2')

    fireEvent.change(screen.getByRole('textbox', { name: 'Etkinlik ara' }), {
      target: { value: '  yazılım   atölyesi  ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Filtreleri uygula' }))

    await waitFor(() =>
      expect(fetchPublicEvents).toHaveBeenLastCalledWith(null, {
        ...emptyFilters,
        query: 'yazılım atölyesi',
      }),
    )
    expect(await screen.findByText('yazılım atölyesi')).toBeInTheDocument()
    expect(await screen.findByText('Sayfa 1')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Kategori' })).toBeEnabled()
  })

  it('renders an explicit empty state', async () => {
    vi.mocked(fetchPublicEvents).mockResolvedValue({
      items: [],
      nextCursor: null,
      hasMore: false,
    })

    renderWithQueryClient(<PublicEventsPage />)

    expect(await screen.findByText('Henüz etkinlik yok')).toBeInTheDocument()
  })

  it('shows a safe error with request ID and retries on demand', async () => {
    vi.mocked(fetchPublicEvents)
      .mockRejectedValueOnce(
        new ApiError('Etkinlikler alınamadı.', { requestId: 'req-public-42' }),
      )
      .mockResolvedValueOnce({
        items: [event],
        nextCursor: null,
        hasMore: false,
      })

    renderWithQueryClient(<PublicEventsPage />)

    expect(
      await screen.findByText('Etkinlikler alınamadı.'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/req-public-42/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }))

    await waitFor(() =>
      expect(screen.getByText(event.title)).toBeInTheDocument(),
    )
    expect(fetchPublicEvents).toHaveBeenCalledTimes(2)
  })
})
