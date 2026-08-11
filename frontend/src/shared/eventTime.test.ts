import { describe, expect, it } from 'vitest'

import {
  eventDateParts,
  formatEventDateTime,
  formatTimeZoneLabel,
} from './eventTime'

describe('event time presentation', () => {
  it('formats the instant in the event timezone', () => {
    expect(
      formatEventDateTime('2035-09-20T16:30:00Z', 'Europe/Istanbul'),
    ).toContain('19:30')
    expect(eventDateParts('2035-09-20T16:30:00Z', 'Europe/Istanbul')).toEqual({
      day: '20',
      month: 'EYL',
    })
  })

  it('presents a readable timezone label without exposing technical syntax', () => {
    expect(formatTimeZoneLabel('2035-09-20T16:30:00Z', 'Europe/Istanbul')).toBe(
      'Istanbul saati (UTC+03:00)',
    )
  })
})
