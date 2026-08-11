import { Stack, Typography } from '@mui/material'

import {
  browserTimeZone,
  formatEventDateTime,
  formatTimeZoneLabel,
} from '../eventTime'

export function EventDateTime({
  startsAt,
  timeZone,
}: {
  startsAt: string
  timeZone: string
}) {
  const localTimeZone = browserTimeZone()
  const showLocalTime = localTimeZone !== timeZone

  return (
    <Stack sx={{ gap: 0.5 }}>
      <Typography sx={{ fontWeight: 760 }}>
        {formatEventDateTime(startsAt, timeZone)}
      </Typography>
      <Typography color="text.secondary" variant="body2">
        {formatTimeZoneLabel(startsAt, timeZone)}
      </Typography>
      {showLocalTime ? (
        <Typography color="text.secondary" variant="caption">
          Sizin saatinizle {formatEventDateTime(startsAt, localTimeZone)}
        </Typography>
      ) : null}
    </Stack>
  )
}
