import { getPublicEvent, listPublicEvents } from './generated'
import type { PublicEventPage, PublicEventResponse } from './generated'
import { toApiError } from './errors'
import './client'

export async function fetchPublicEvents(
  cursor: string | null,
): Promise<PublicEventPage> {
  try {
    const result = await listPublicEvents({
      query: { cursor, limit: 12 },
      throwOnError: true,
    })
    return result.data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function fetchPublicEvent(
  eventId: string,
): Promise<PublicEventResponse> {
  try {
    const result = await getPublicEvent({
      path: { event_id: eventId },
      throwOnError: true,
    })
    return result.data
  } catch (error) {
    throw toApiError(error)
  }
}
