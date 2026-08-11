export interface LocationOption {
  value: string
  group: string
  detail: string
  kind: 'Şehir' | 'Çevrim içi'
  timezone?: string
}

const city = (
  value: string,
  detail = 'Türkiye',
  timezone = detail === 'Türkiye' ? 'Europe/Istanbul' : undefined,
): LocationOption => ({
  value,
  group: detail === 'Türkiye' ? 'Türkiye' : 'Yurt dışı',
  detail,
  kind: 'Şehir',
  timezone,
})

const online = (value: string, detail: string): LocationOption => ({
  value,
  group: 'Çevrim içi',
  detail,
  kind: 'Çevrim içi',
})

export const LOCATION_OPTIONS = [
  city('İstanbul'),
  city('Ankara'),
  city('İzmir'),
  city('Bursa'),
  city('Antalya'),
  city('Eskişehir'),
  city('Kocaeli'),
  city('Adana'),
  city('Konya'),
  city('Gaziantep'),
  city('Mersin'),
  city('Kayseri'),
  city('Samsun'),
  city('Trabzon'),
  city('Diyarbakır'),
  city('Şanlıurfa'),
  city('Denizli'),
  city('Muğla'),
  city('Balıkesir'),
  city('Çanakkale'),
  city('Sakarya'),
  city('Tekirdağ'),
  city('Hatay'),
  city('Berlin', 'Almanya', 'Europe/Berlin'),
  city('Londra', 'Birleşik Krallık', 'Europe/London'),
  city('Paris', 'Fransa', 'Europe/Paris'),
  city('Amsterdam', 'Hollanda', 'Europe/Amsterdam'),
  city('Dubai', 'Birleşik Arap Emirlikleri', 'Asia/Dubai'),
  city('New York', 'ABD', 'America/New_York'),
  online('Çevrim içi', 'Platform daha sonra paylaşılacak'),
  online('Zoom', 'Canlı video etkinliği'),
  online('Google Meet', 'Canlı video etkinliği'),
  online('Microsoft Teams', 'Canlı video etkinliği'),
  online('YouTube Live', 'Canlı yayın'),
] as const satisfies readonly LocationOption[]

export interface TimezoneOption {
  value: string
  city: string
  country: string
  group: string
  aliases?: string
}

export const TIMEZONE_OPTIONS = [
  {
    value: 'Europe/Istanbul',
    city: 'İstanbul',
    country: 'Türkiye',
    group: 'Türkiye ve yakın bölgeler',
    aliases: 'Ankara İzmir Bursa Antalya TRT Türkiye saati',
  },
  {
    value: 'Europe/Athens',
    city: 'Atina',
    country: 'Yunanistan',
    group: 'Türkiye ve yakın bölgeler',
  },
  {
    value: 'Europe/Sofia',
    city: 'Sofya',
    country: 'Bulgaristan',
    group: 'Türkiye ve yakın bölgeler',
  },
  {
    value: 'Europe/Bucharest',
    city: 'Bükreş',
    country: 'Romanya',
    group: 'Türkiye ve yakın bölgeler',
  },
  {
    value: 'Asia/Nicosia',
    city: 'Lefkoşa',
    country: 'Kıbrıs',
    group: 'Türkiye ve yakın bölgeler',
  },
  {
    value: 'Europe/London',
    city: 'Londra',
    country: 'Birleşik Krallık',
    group: 'Avrupa',
    aliases: 'İngiltere GMT BST',
  },
  {
    value: 'Europe/Dublin',
    city: 'Dublin',
    country: 'İrlanda',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Lisbon',
    city: 'Lizbon',
    country: 'Portekiz',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Paris',
    city: 'Paris',
    country: 'Fransa',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Berlin',
    city: 'Berlin',
    country: 'Almanya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Amsterdam',
    city: 'Amsterdam',
    country: 'Hollanda',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Brussels',
    city: 'Brüksel',
    country: 'Belçika',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Madrid',
    city: 'Madrid',
    country: 'İspanya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Rome',
    city: 'Roma',
    country: 'İtalya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Zurich',
    city: 'Zürih',
    country: 'İsviçre',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Vienna',
    city: 'Viyana',
    country: 'Avusturya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Prague',
    city: 'Prag',
    country: 'Çekya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Warsaw',
    city: 'Varşova',
    country: 'Polonya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Budapest',
    city: 'Budapeşte',
    country: 'Macaristan',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Belgrade',
    city: 'Belgrad',
    country: 'Sırbistan',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Copenhagen',
    city: 'Kopenhag',
    country: 'Danimarka',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Stockholm',
    city: 'Stockholm',
    country: 'İsveç',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Oslo',
    city: 'Oslo',
    country: 'Norveç',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Helsinki',
    city: 'Helsinki',
    country: 'Finlandiya',
    group: 'Avrupa',
  },
  {
    value: 'Europe/Kyiv',
    city: 'Kiev',
    country: 'Ukrayna',
    group: 'Avrupa',
    aliases: 'Kyiv',
  },
  {
    value: 'Europe/Moscow',
    city: 'Moskova',
    country: 'Rusya',
    group: 'Avrupa',
  },
  {
    value: 'Asia/Dubai',
    city: 'Dubai',
    country: 'Birleşik Arap Emirlikleri',
    group: 'Orta Doğu ve Afrika',
    aliases: 'BAE Körfez saati GST',
  },
  {
    value: 'Asia/Riyadh',
    city: 'Riyad',
    country: 'Suudi Arabistan',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Jerusalem',
    city: 'Kudüs',
    country: 'İsrail',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Beirut',
    city: 'Beyrut',
    country: 'Lübnan',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Baku',
    city: 'Bakü',
    country: 'Azerbaycan',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Tbilisi',
    city: 'Tiflis',
    country: 'Gürcistan',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Tehran',
    city: 'Tahran',
    country: 'İran',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Africa/Cairo',
    city: 'Kahire',
    country: 'Mısır',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Africa/Casablanca',
    city: 'Kazablanka',
    country: 'Fas',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Africa/Johannesburg',
    city: 'Johannesburg',
    country: 'Güney Afrika',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Africa/Nairobi',
    city: 'Nairobi',
    country: 'Kenya',
    group: 'Orta Doğu ve Afrika',
  },
  {
    value: 'Asia/Karachi',
    city: 'Karaçi',
    country: 'Pakistan',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Kolkata',
    city: 'Kalküta',
    country: 'Hindistan',
    group: 'Asya ve Pasifik',
    aliases: 'Delhi Mumbai IST',
  },
  {
    value: 'Asia/Dhaka',
    city: 'Dakka',
    country: 'Bangladeş',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Bangkok',
    city: 'Bangkok',
    country: 'Tayland',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Jakarta',
    city: 'Cakarta',
    country: 'Endonezya',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Singapore',
    city: 'Singapur',
    country: 'Singapur',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Hong_Kong',
    city: 'Hong Kong',
    country: 'Hong Kong',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Shanghai',
    city: 'Şanghay',
    country: 'Çin',
    group: 'Asya ve Pasifik',
    aliases: 'Pekin Beijing',
  },
  {
    value: 'Asia/Tokyo',
    city: 'Tokyo',
    country: 'Japonya',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Asia/Seoul',
    city: 'Seul',
    country: 'Güney Kore',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Australia/Perth',
    city: 'Perth',
    country: 'Avustralya',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Australia/Sydney',
    city: 'Sidney',
    country: 'Avustralya',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Australia/Melbourne',
    city: 'Melbourne',
    country: 'Avustralya',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'Pacific/Auckland',
    city: 'Auckland',
    country: 'Yeni Zelanda',
    group: 'Asya ve Pasifik',
  },
  {
    value: 'America/New_York',
    city: 'New York',
    country: 'ABD',
    group: 'Amerika',
    aliases: 'Doğu Amerika EST EDT',
  },
  {
    value: 'America/Chicago',
    city: 'Chicago',
    country: 'ABD',
    group: 'Amerika',
    aliases: 'Merkez Amerika CST CDT',
  },
  {
    value: 'America/Denver',
    city: 'Denver',
    country: 'ABD',
    group: 'Amerika',
    aliases: 'Dağ saati MST MDT',
  },
  {
    value: 'America/Los_Angeles',
    city: 'Los Angeles',
    country: 'ABD',
    group: 'Amerika',
    aliases: 'Batı Amerika PST PDT San Francisco Seattle',
  },
  {
    value: 'America/Toronto',
    city: 'Toronto',
    country: 'Kanada',
    group: 'Amerika',
  },
  {
    value: 'America/Vancouver',
    city: 'Vancouver',
    country: 'Kanada',
    group: 'Amerika',
  },
  {
    value: 'America/Mexico_City',
    city: 'Meksiko',
    country: 'Meksika',
    group: 'Amerika',
  },
  {
    value: 'America/Bogota',
    city: 'Bogota',
    country: 'Kolombiya',
    group: 'Amerika',
  },
  {
    value: 'America/Lima',
    city: 'Lima',
    country: 'Peru',
    group: 'Amerika',
  },
  {
    value: 'America/Santiago',
    city: 'Santiago',
    country: 'Şili',
    group: 'Amerika',
  },
  {
    value: 'America/Sao_Paulo',
    city: 'São Paulo',
    country: 'Brezilya',
    group: 'Amerika',
  },
  {
    value: 'America/Argentina/Buenos_Aires',
    city: 'Buenos Aires',
    country: 'Arjantin',
    group: 'Amerika',
  },
  {
    value: 'UTC',
    city: 'UTC',
    country: 'Eşgüdümlü Evrensel Zaman',
    group: 'Evrensel',
    aliases: 'GMT Zulu sıfır',
  },
] as const satisfies readonly TimezoneOption[]

export function timezoneOffsetLabel(value: string, date = new Date()) {
  try {
    const offset = new Intl.DateTimeFormat('tr-TR', {
      timeZone: value,
      timeZoneName: 'longOffset',
    })
      .formatToParts(date)
      .find((part) => part.type === 'timeZoneName')?.value
    if (!offset || offset === 'GMT') return 'UTC+00:00'
    return offset.replace('GMT', 'UTC')
  } catch {
    return 'UTC'
  }
}

export function timezoneLocalTimeLabel(value: string, date = new Date()) {
  try {
    return new Intl.DateTimeFormat('tr-TR', {
      timeZone: value,
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    }).format(date)
  } catch {
    return '--:--'
  }
}

export function timezoneOptionLabel(option: TimezoneOption) {
  return `${option.city}, ${option.country} (${timezoneOffsetLabel(option.value)})`
}

export function timezoneSearchText(option: TimezoneOption) {
  return [
    option.city,
    option.country,
    option.value,
    option.group,
    option.aliases,
    timezoneOffsetLabel(option.value),
  ]
    .filter(Boolean)
    .join(' ')
}

export function timezoneOption(value: string): TimezoneOption {
  return (
    TIMEZONE_OPTIONS.find((option) => option.value === value) ?? {
      value,
      city: value.split('/').at(-1)?.replaceAll('_', ' ') || value,
      country: 'Özel saat dilimi',
      group: 'Diğer',
      aliases: value,
    }
  )
}
