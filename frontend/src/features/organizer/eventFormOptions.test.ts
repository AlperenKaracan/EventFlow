import { describe, expect, it } from 'vitest'

import {
  LOCATION_OPTIONS,
  TIMEZONE_OPTIONS,
  timezoneOffsetLabel,
  timezoneOption,
  timezoneOptionLabel,
  timezoneSearchText,
} from './eventFormOptions'

describe('event form timezone options', () => {
  it('offers a broad and duplicate-free IANA timezone selection', () => {
    const values = TIMEZONE_OPTIONS.map((option) => option.value)

    expect(values.length).toBeGreaterThanOrEqual(60)
    expect(new Set(values).size).toBe(values.length)
    expect(values).toContain('Europe/Istanbul')
    expect(values).toContain('America/New_York')
    expect(values).toContain('Asia/Tokyo')
    expect(values).toContain('UTC')
  })

  it('formats the selected city with its UTC offset', () => {
    const option = timezoneOption('Europe/Istanbul')

    expect(
      timezoneOffsetLabel(option.value, new Date('2026-01-15T12:00:00.000Z')),
    ).toBe('UTC+03:00')
    expect(timezoneOptionLabel(option)).toMatch(
      /^İstanbul, Türkiye \(UTC\+03:00\)$/,
    )
  })

  it('indexes Turkish aliases, IANA identifiers, and UTC offsets', () => {
    const option = timezoneOption('America/Los_Angeles')
    const searchText = timezoneSearchText(option)

    expect(searchText).toContain('Batı Amerika')
    expect(searchText).toContain('America/Los_Angeles')
    expect(searchText).toContain('UTC')
  })

  it('keeps an existing custom IANA value readable', () => {
    expect(timezoneOption('Atlantic/Reykjavik')).toMatchObject({
      value: 'Atlantic/Reykjavik',
      city: 'Reykjavik',
      country: 'Özel saat dilimi',
      group: 'Diğer',
    })
  })
})

describe('event form location options', () => {
  it('groups useful city and online suggestions without duplicates', () => {
    const values = LOCATION_OPTIONS.map((option) => option.value)

    expect(values.length).toBeGreaterThanOrEqual(30)
    expect(new Set(values).size).toBe(values.length)
    expect(LOCATION_OPTIONS).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          value: 'İstanbul',
          kind: 'Şehir',
          group: 'Türkiye',
          timezone: 'Europe/Istanbul',
        }),
        expect.objectContaining({
          value: 'Berlin',
          group: 'Yurt dışı',
          timezone: 'Europe/Berlin',
        }),
        expect.objectContaining({
          value: 'Zoom',
          kind: 'Çevrim içi',
          group: 'Çevrim içi',
        }),
      ]),
    )
  })
})
