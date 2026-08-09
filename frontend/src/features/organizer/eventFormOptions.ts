export const LOCATION_OPTIONS = [
  'İstanbul',
  'Ankara',
  'İzmir',
  'Bursa',
  'Antalya',
  'Eskişehir',
  'Kocaeli',
  'Adana',
  'Konya',
  'Gaziantep',
  'Çevrim içi',
] as const

export const TIMEZONE_OPTIONS = [
  { value: 'Europe/Istanbul', label: 'İstanbul — Türkiye saati (UTC+03:00)' },
  { value: 'Europe/London', label: 'Londra — Birleşik Krallık' },
  { value: 'Europe/Berlin', label: 'Berlin — Orta Avrupa' },
  { value: 'Europe/Paris', label: 'Paris — Orta Avrupa' },
  { value: 'Asia/Dubai', label: 'Dubai — Körfez saati (UTC+04:00)' },
  { value: 'America/New_York', label: 'New York — Doğu Amerika' },
  { value: 'America/Los_Angeles', label: 'Los Angeles — Batı Amerika' },
] as const

export function timezoneOption(value: string) {
  return (
    TIMEZONE_OPTIONS.find((option) => option.value === value) ?? {
      value,
      label: value,
    }
  )
}
