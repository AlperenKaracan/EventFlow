const dateOptions: Intl.DateTimeFormatOptions = {
  dateStyle: 'full',
  timeStyle: 'short',
}

export function formatEventDateTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat('tr-TR', { ...dateOptions, timeZone }).format(
    new Date(value),
  )
}

export function formatShortEventDateTime(
  value: string,
  timeZone: string,
): string {
  return new Intl.DateTimeFormat('tr-TR', {
    day: 'numeric',
    month: 'long',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone,
  }).format(new Date(value))
}

export function eventDateParts(value: string, timeZone: string) {
  const parts = new Intl.DateTimeFormat('tr-TR', {
    day: '2-digit',
    month: 'short',
    timeZone,
  }).formatToParts(new Date(value))
  const get = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? ''
  return {
    day: get('day'),
    month: get('month').replace('.', '').toLocaleUpperCase('tr-TR'),
  }
}

export function formatTimeZoneLabel(value: string, timeZone: string): string {
  const offset = new Intl.DateTimeFormat('tr-TR', {
    timeZone,
    timeZoneName: 'longOffset',
  })
    .formatToParts(new Date(value))
    .find((part) => part.type === 'timeZoneName')?.value

  const city = timeZone.split('/').at(-1)?.replaceAll('_', ' ') ?? timeZone
  return `${city} saati${offset ? ` (${offset.replace('GMT', 'UTC')})` : ''}`
}

export function browserTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}
