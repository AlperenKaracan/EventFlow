import {
  cancelReservation,
  createReservation,
  listMyReservations,
} from './generated'
import type {
  ReservationHistoryPage,
  ReservationHistoryResponse,
  ReservationMutationResponse,
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

export interface ReservationIntent {
  eventId: string
  idempotencyKey: string
}

export function createReservationIntent(eventId: string): ReservationIntent {
  return { eventId, idempotencyKey: crypto.randomUUID() }
}

export const reserveEvent = (
  intent: ReservationIntent,
): Promise<ReservationMutationResponse> =>
  guarded(() =>
    createReservation({
      path: { event_id: intent.eventId },
      headers: { 'Idempotency-Key': intent.idempotencyKey },
      throwOnError: true,
    }),
  )

export const fetchMyReservations = (
  cursor: string | null,
): Promise<ReservationHistoryPage> =>
  guarded(() =>
    listMyReservations({ query: { cursor, limit: 12 }, throwOnError: true }),
  )

export async function fetchActiveReservationForEvent(
  eventId: string,
): Promise<ReservationHistoryResponse | null> {
  let cursor: string | null = null

  do {
    const page: ReservationHistoryPage = await guarded(() =>
      listMyReservations({
        query: { cursor, limit: 100 },
        throwOnError: true,
      }),
    )
    const activeReservation = page.items.find(
      (reservation) =>
        reservation.event.id === eventId && reservation.status === 'ACTIVE',
    )
    if (activeReservation) return activeReservation
    cursor = page.nextCursor
  } while (cursor)

  return null
}

export async function cancelMyReservation(
  reservationId: string,
): Promise<void> {
  await guarded(() =>
    cancelReservation({
      path: { reservation_id: reservationId },
      throwOnError: true,
    }),
  )
}
