type ApiErrorResponse = {
  error?: string
  detail?: string
  message?: string
}

type ApiErrorLike = {
  response?: {
    data?: ApiErrorResponse | string
  }
}

/**
 * Extract a user-friendly message from an Axios-like API error.
 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  const maybeError = error as ApiErrorLike
  const data = maybeError?.response?.data

  if (typeof data === 'string' && data.trim().length > 0) {
    return data
  }

  if (data && typeof data === 'object') {
    if (typeof data.error === 'string' && data.error.trim().length > 0) return data.error
    if (typeof data.detail === 'string' && data.detail.trim().length > 0) return data.detail
    if (typeof data.message === 'string' && data.message.trim().length > 0) return data.message
  }

  return fallback
}
