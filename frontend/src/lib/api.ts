import { clearAccessToken, getAccessToken } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

type ErrorPayload = {
  detail?: string | Array<{ msg?: string }>
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function errorMessage(payload: ErrorPayload | null, fallback: string) {
  if (typeof payload?.detail === 'string') {
    return payload.detail
  }
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg).filter(Boolean).join(', ')
  }
  return fallback
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken()
  const headers = new Headers(options.headers)

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const payload = await response
      .json()
      .then((body) => body as ErrorPayload)
      .catch(() => null)
    if (response.status === 401) {
      clearAccessToken()
    }
    throw new ApiError(
      errorMessage(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}
