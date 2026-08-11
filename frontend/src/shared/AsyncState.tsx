import { Alert, Box, Button, Skeleton, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

import { ApiError } from '../api/errors'

export function LoadingState({ label = 'Yükleniyor' }: { label?: string }) {
  return (
    <Stack
      role="status"
      aria-label={label}
      sx={{
        gap: 1.5,
        mt: 4,
        py: 2,
      }}
    >
      <Typography color="text.secondary" variant="body2">
        {label}
      </Typography>
      <Skeleton height={26} width="42%" />
      <Skeleton height={18} width="72%" />
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ gap: 2, pt: 1 }}>
        {[0, 1, 2].map((item) => (
          <Skeleton
            key={item}
            height={190}
            sx={{ flex: 1, transform: 'none' }}
            variant="rounded"
          />
        ))}
      </Stack>
    </Stack>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <Box
      sx={{
        border: '1px dashed',
        borderColor: 'divider',
        borderRadius: 4,
        mt: 4,
        px: 3,
        py: 8,
        textAlign: 'center',
      }}
    >
      <Typography component="h2" variant="h5" sx={{ fontWeight: 750 }}>
        {title}
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1 }}>
        {description}
      </Typography>
      {action ? <Box sx={{ mt: 3 }}>{action}</Box> : null}
    </Box>
  )
}

export function ErrorState({
  error,
  onRetry,
  title,
  description,
}: {
  error: unknown
  onRetry?: () => void
  title?: string
  description?: string
}) {
  const apiError = error instanceof ApiError ? error : undefined
  const knownError = apiError?.code ? friendlyErrors[apiError.code] : undefined
  const visibleTitle = title ?? knownError?.title ?? 'İşlem tamamlanamadı'
  const visibleDescription =
    description ??
    knownError?.description ??
    apiError?.message ??
    'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.'

  return (
    <Alert
      severity="error"
      action={
        onRetry ? (
          <Button color="inherit" onClick={onRetry}>
            Tekrar dene
          </Button>
        ) : undefined
      }
    >
      <Typography component="h2" sx={{ fontWeight: 700 }}>
        {visibleTitle}
      </Typography>
      <Typography variant="body2">{visibleDescription}</Typography>
    </Alert>
  )
}

const friendlyErrors: Record<string, { title: string; description: string }> = {
  EVENT_FULL: {
    title: 'Etkinlikte yer kalmadı',
    description:
      'Bu etkinliğin kontenjanı dolu. Daha sonra yeniden kontrol edebilir veya başka bir etkinlik seçebilirsiniz.',
  },
  RESOURCE_NOT_FOUND: {
    title: 'İçerik artık kullanılamıyor',
    description:
      'İçerik iptal edilmiş, kaldırılmış veya erişiminize kapatılmış olabilir.',
  },
  RATE_LIMIT_EXCEEDED: {
    title: 'Çok fazla işlem yapıldı',
    description: 'Kısa bir süre bekleyip yeniden deneyin.',
  },
}
