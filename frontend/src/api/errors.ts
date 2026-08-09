import type { ErrorEnvelope } from './generated'

export class ApiError extends Error {
  readonly code?: string
  readonly requestId?: string

  constructor(
    message: string,
    options?: { code?: string; requestId?: string },
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = options?.code
    this.requestId = options?.requestId
  }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (!value || typeof value !== 'object' || !('error' in value)) return false
  const error = value.error
  return Boolean(
    error &&
    typeof error === 'object' &&
    'message' in error &&
    typeof error.message === 'string',
  )
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (isErrorEnvelope(error)) {
    return new ApiError(error.error.message, {
      code: error.error.code,
      requestId: error.error.requestId,
    })
  }
  return new ApiError('İstek tamamlanamadı. Lütfen tekrar deneyin.')
}
