import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material'

import { ApiError } from '../api/errors'

export function LoadingState({ label = 'Yükleniyor' }: { label?: string }) {
  return (
    <Stack
      role="status"
      sx={{
        alignItems: 'center',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 3,
        gap: 2,
        mt: 4,
        py: 8,
      }}
    >
      <CircularProgress aria-hidden="true" />
      <Typography>{label}</Typography>
    </Stack>
  )
}

export function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <Box
      sx={{
        border: '1px dashed',
        borderColor: 'divider',
        borderRadius: 3,
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
