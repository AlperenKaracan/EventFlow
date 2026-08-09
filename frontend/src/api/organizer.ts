import {
  cancelEvent,
  createEvent,
  getOwnedEvent,
  listCategories,
  listEventAttendees,
  listOwnedEvents,
  updateEvent,
} from './generated'
import type {
  CategoryResponse,
  EventAttendeePage,
  EventCreateRequest,
  EventUpdateRequest,
  OwnerEventPage,
  OwnerEventResponse,
} from './generated'
import { toApiError } from './errors'
import './client'

async function guarded<T>(request: () => Promise<{ data: T }>): Promise<T> {
  try {
    return (await request()).data
  } catch (error) {
    throw toApiError(error)
  }
}

export const fetchCategories = (): Promise<Array<CategoryResponse>> =>
  guarded(() => listCategories({ throwOnError: true }))

export const fetchOwnedEvents = (
  cursor: string | null,
): Promise<OwnerEventPage> =>
  guarded(() =>
    listOwnedEvents({ query: { cursor, limit: 12 }, throwOnError: true }),
  )

export const fetchOwnedEvent = (eventId: string): Promise<OwnerEventResponse> =>
  guarded(() =>
    getOwnedEvent({ path: { event_id: eventId }, throwOnError: true }),
  )

export const createOwnedEvent = (
  input: EventCreateRequest,
): Promise<OwnerEventResponse> =>
  guarded(() => createEvent({ body: input, throwOnError: true }))

export const updateOwnedEvent = (
  eventId: string,
  input: EventUpdateRequest,
): Promise<OwnerEventResponse> =>
  guarded(() =>
    updateEvent({
      body: input,
      path: { event_id: eventId },
      throwOnError: true,
    }),
  )

export async function cancelOwnedEvent(
  eventId: string,
  expectedVersion: number,
): Promise<void> {
  await guarded(() =>
    cancelEvent({
      path: { event_id: eventId },
      query: { expectedVersion },
      throwOnError: true,
    }),
  )
}

export const fetchEventAttendees = (
  eventId: string,
  cursor: string | null,
): Promise<EventAttendeePage> =>
  guarded(() =>
    listEventAttendees({
      path: { event_id: eventId },
      query: { cursor, limit: 25 },
      throwOnError: true,
    }),
  )
