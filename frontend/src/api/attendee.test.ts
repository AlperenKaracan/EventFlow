import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  cancelReservation: vi.fn(),
  createReservation: vi.fn(),
  listMyReservations: vi.fn(),
}))

vi.mock('./generated', () => mocks)
vi.mock('./client', () => ({}))

import {
  createReservationIntent,
  fetchActiveReservationForEvent,
  reserveEvent,
} from './attendee'

describe('attendee API boundary', () => {
  beforeEach(() => {
    Object.values(mocks).forEach((mock) => mock.mockReset())
  })

  it('creates a new idempotency key for each intentional submit', () => {
    const first = createReservationIntent('event-1')
    const second = createReservationIntent('event-1')

    expect(first.idempotencyKey).not.toBe(second.idempotencyKey)
  })

  it('passes the intent idempotency key unchanged to the SDK', async () => {
    mocks.createReservation.mockResolvedValue({ data: { id: 'reservation-1' } })
    const intent = {
      eventId: 'event-1',
      idempotencyKey: '10000000-0000-4000-8000-000000000001',
    }

    await expect(reserveEvent(intent)).resolves.toEqual({ id: 'reservation-1' })
    expect(mocks.createReservation).toHaveBeenCalledWith({
      path: { event_id: 'event-1' },
      headers: { 'Idempotency-Key': intent.idempotencyKey },
      throwOnError: true,
    })
  })

  it('finds an active reservation across history pages', async () => {
    const activeReservation = {
      id: 'reservation-2',
      status: 'ACTIVE',
      event: { id: 'event-2' },
    }
    mocks.listMyReservations
      .mockResolvedValueOnce({
        data: {
          items: [
            {
              id: 'reservation-1',
              status: 'CANCELLED_BY_ATTENDEE',
              event: { id: 'event-1' },
            },
          ],
          nextCursor: 'next-page',
          hasMore: true,
        },
      })
      .mockResolvedValueOnce({
        data: {
          items: [activeReservation],
          nextCursor: null,
          hasMore: false,
        },
      })

    await expect(fetchActiveReservationForEvent('event-2')).resolves.toEqual(
      activeReservation,
    )
    expect(mocks.listMyReservations).toHaveBeenNthCalledWith(1, {
      query: { cursor: null, limit: 100 },
      throwOnError: true,
    })
    expect(mocks.listMyReservations).toHaveBeenNthCalledWith(2, {
      query: { cursor: 'next-page', limit: 100 },
      throwOnError: true,
    })
  })
})
