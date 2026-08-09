function zonedParts(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const values = Object.fromEntries(
    parts.map((part) => [part.type, part.value]),
  )
  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
    hour: Number(values.hour),
    minute: Number(values.minute),
    second: Number(values.second),
  }
}

function offsetMilliseconds(date: Date, timeZone: string): number {
  const parts = zonedParts(date, timeZone)
  return (
    Date.UTC(
      parts.year,
      parts.month - 1,
      parts.day,
      parts.hour,
      parts.minute,
      parts.second,
    ) - date.getTime()
  )
}

function formatOffset(offsetMinutes: number): string {
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const absolute = Math.abs(offsetMinutes)
  const hours = String(Math.floor(absolute / 60)).padStart(2, '0')
  const minutes = String(absolute % 60).padStart(2, '0')
  return `${sign}${hours}:${minutes}`
}

export function localDateTimeToZonedIso(
  value: string,
  timeZone: string,
): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value)
  if (!match) throw new Error('Başlangıç zamanı geçersiz.')
  const [, year, month, day, hour, minute] = match
  const wallClockUtc = Date.UTC(
    Number(year),
    Number(month) - 1,
    Number(day),
    Number(hour),
    Number(minute),
  )
  let instant = new Date(wallClockUtc)
  for (let iteration = 0; iteration < 2; iteration += 1) {
    instant = new Date(wallClockUtc - offsetMilliseconds(instant, timeZone))
  }
  const rendered = zonedParts(instant, timeZone)
  if (
    rendered.year !== Number(year) ||
    rendered.month !== Number(month) ||
    rendered.day !== Number(day) ||
    rendered.hour !== Number(hour) ||
    rendered.minute !== Number(minute)
  ) {
    throw new Error('Bu yerel saat seçilen saat diliminde geçerli değil.')
  }
  const offsetMinutes = Math.round(
    offsetMilliseconds(instant, timeZone) / 60_000,
  )
  return `${value}:00${formatOffset(offsetMinutes)}`
}

export function zonedIsoToLocalDateTime(
  value: string,
  timeZone: string,
): string {
  const parts = zonedParts(new Date(value), timeZone)
  const twoDigits = (number: number) => String(number).padStart(2, '0')
  return `${parts.year}-${twoDigits(parts.month)}-${twoDigits(parts.day)}T${twoDigits(parts.hour)}:${twoDigits(parts.minute)}`
}
