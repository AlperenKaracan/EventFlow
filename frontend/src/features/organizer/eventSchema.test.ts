import { describe, expect, it } from 'vitest'

import { eventFormSchema } from './eventSchema'

const validEvent = {
  categoryId: '20000000-0000-7000-8000-000000000001',
  title: 'EventFlow Buluşması',
  description: 'Açıklama',
  location: 'İstanbul',
  startsAt: '2035-05-12T19:00',
  timezone: 'Europe/Istanbul',
  capacity: '120',
}

describe('organizer event schema', () => {
  it('coerces a positive integer capacity and trims required text', () => {
    const result = eventFormSchema.parse({ ...validEvent, title: '  Başlık  ' })

    expect(result.capacity).toBe(120)
    expect(result.title).toBe('Başlık')
  })

  it.each(['0', '-1', '1.5'])('rejects invalid capacity %s', (capacity) => {
    expect(eventFormSchema.safeParse({ ...validEvent, capacity }).success).toBe(
      false,
    )
  })

  it('matches backend title and description length limits', () => {
    const result = eventFormSchema.safeParse({
      ...validEvent,
      title: 'x'.repeat(161),
      description: 'x'.repeat(5001),
    })

    expect(result.success).toBe(false)
  })
})
