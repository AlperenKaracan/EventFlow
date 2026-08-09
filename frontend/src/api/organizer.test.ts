import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  cancelEvent: vi.fn(),
  createEvent: vi.fn(),
  getOwnedEvent: vi.fn(),
  listCategories: vi.fn(),
  listEventAttendees: vi.fn(),
  listOwnedEvents: vi.fn(),
  updateEvent: vi.fn(),
}))

vi.mock('./generated', () => mocks)
vi.mock('./client', () => ({}))

import { cancelOwnedEvent, fetchOwnedEvent } from './organizer'

describe('organizer API boundary', () => {
  beforeEach(() => {
    Object.values(mocks).forEach((mock) => mock.mockReset())
  })

  it('uses the owner-only detail endpoint with the requested event ID', async () => {
    mocks.getOwnedEvent.mockResolvedValue({ data: { id: 'event-owner' } })

    await expect(fetchOwnedEvent('event-owner')).resolves.toEqual({
      id: 'event-owner',
    })
    expect(mocks.getOwnedEvent).toHaveBeenCalledWith({
      path: { event_id: 'event-owner' },
      throwOnError: true,
    })
  })

  it('sends the current version when cancelling an event', async () => {
    mocks.cancelEvent.mockResolvedValue({ data: undefined })

    await expect(cancelOwnedEvent('event-42', 7)).resolves.toBeUndefined()
    expect(mocks.cancelEvent).toHaveBeenCalledWith({
      path: { event_id: 'event-42' },
      query: { expectedVersion: 7 },
      throwOnError: true,
    })
  })
})
