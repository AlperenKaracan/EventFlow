import { describe, expect, it } from 'vitest'

import { localDateTimeToZonedIso, zonedIsoToLocalDateTime } from './timezone'

describe('timezone conversion', () => {
  it('keeps Istanbul wall time with its +03:00 offset', () => {
    expect(localDateTimeToZonedIso('2035-09-20T19:30', 'Europe/Istanbul')).toBe(
      '2035-09-20T19:30:00+03:00',
    )
  })

  it('respects daylight-saving offsets', () => {
    expect(
      localDateTimeToZonedIso('2035-01-20T19:30', 'Europe/Berlin').endsWith(
        '+01:00',
      ),
    ).toBe(true)
    expect(
      localDateTimeToZonedIso('2035-07-20T19:30', 'Europe/Berlin').endsWith(
        '+02:00',
      ),
    ).toBe(true)
  })

  it('renders an instant back in the selected event timezone', () => {
    expect(
      zonedIsoToLocalDateTime('2035-09-20T16:30:00Z', 'Europe/Istanbul'),
    ).toBe('2035-09-20T19:30')
  })
})
