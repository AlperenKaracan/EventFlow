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
}: {
  error: unknown
  onRetry: () => void
}) {
  const apiError = error instanceof ApiError ? error : undefined

  return (
    <Alert
      severity="error"
      action={
        <Button color="inherit" onClick={onRetry}>
          Tekrar dene
        </Button>
      }
    >
      <Typography sx={{ fontWeight: 700 }}>İstek tamamlanamadı</Typography>
      <Typography variant="body2">
        {apiError?.message ?? 'Beklenmeyen bir hata oluştu.'}
      </Typography>
      {apiError?.requestId ? (
        <Typography variant="caption" component="p" sx={{ mt: 1 }}>
          İstek kimliği: <code>{apiError.requestId}</code>
        </Typography>
      ) : null}
    </Alert>
  )
}
