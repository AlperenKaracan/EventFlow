import { getPublicEvent, listCategories, listPublicEvents } from './generated'
import type {
  CategoryResponse,
  PublicEventPage,
  PublicEventResponse,
} from './generated'
import { toApiError } from './errors'
import './client'

export interface PublicEventFilters {
  query: string
  category: string
  dateFrom: string
  dateTo: string
}

export async function fetchPublicEvents(
  cursor: string | null,
  filters: PublicEventFilters,
): Promise<PublicEventPage> {
  try {
    const result = await listPublicEvents({
      query: {
        cursor,
        limit: 12,
        q: filters.query || undefined,
        category: filters.category || undefined,
        dateFrom: filters.dateFrom || undefined,
        dateTo: filters.dateTo || undefined,
      },
      throwOnError: true,
    })
    return result.data
  } catch (error) {
    throw toApiError(error)
  }
}

export async function fetchPublicCategories(): Promise<
  Array<CategoryResponse>
> {
  try {
    const result = await listCategories({ throwOnError: true })
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
