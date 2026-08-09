import {
  cancelReservation,
  createReservation,
  listMyReservations,
} from './generated'
import type {
  ReservationHistoryPage,
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
