import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  UserResponse,
} from '../api/generated'
import {
  loginUser,
  logoutUser,
  refreshSession,
  registerUser,
} from '../api/generated'
import { client } from '../api/client'
import { toApiError } from '../api/errors'

export type SessionState =
  | { status: 'bootstrapping'; user: null }
  | { status: 'anonymous'; user: null }
  | { status: 'authenticated'; user: UserResponse }

let accessToken: string | null = null
let state: SessionState = { status: 'bootstrapping', user: null }
let refreshInFlight: Promise<LoginResponse | null> | null = null
let bootstrapInFlight: Promise<void> | null = null
const listeners = new Set<() => void>()

function publish(nextState: SessionState) {
  state = nextState
  listeners.forEach((listener) => listener())
}

function acceptSession(session: LoginResponse) {
  accessToken = session.accessToken
  publish({ status: 'authenticated', user: session.user })
}

function rejectSession() {
  accessToken = null
  publish({ status: 'anonymous', user: null })
}

export function getSessionSnapshot(): SessionState {
  return state
}

export function subscribeToSession(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getAccessToken(): string | null {
  return accessToken
}

export function clearSession() {
  rejectSession()
}

export function refreshAccessToken(): Promise<LoginResponse | null> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    try {
      const result = await refreshSession({ throwOnError: true })
      acceptSession(result.data)
      return result.data
    } catch {
      rejectSession()
      return null
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

export function bootstrapSession(): Promise<void> {
  if (state.status !== 'bootstrapping') return Promise.resolve()
  if (bootstrapInFlight) return bootstrapInFlight

  bootstrapInFlight = refreshAccessToken().then(() => undefined)
  return bootstrapInFlight
}

export async function login(credentials: LoginRequest): Promise<UserResponse> {
  try {
    const result = await loginUser({ body: credentials, throwOnError: true })
    acceptSession(result.data)
    return result.data.user
  } catch (error) {
    throw toApiError(error)
  }
}

export async function registerAndLogin(
  input: RegisterRequest,
): Promise<UserResponse> {
  try {
    await registerUser({ body: input, throwOnError: true })
  } catch (error) {
    throw toApiError(error)
  }

  return login({ email: input.email, password: input.password })
}

export async function logout(): Promise<void> {
  try {
    await logoutUser({ throwOnError: true })
  } catch (error) {
    throw toApiError(error)
  } finally {
    rejectSession()
  }
}

client.interceptors.request.use((request, options) => {
  if (!accessToken || !options.security?.length) return request
  const headers = new Headers(request.headers)
  headers.set('Authorization', `Bearer ${accessToken}`)
  return new Request(request, { headers })
})

client.interceptors.response.use(async (response, request, options) => {
  const isRefreshRequest = new URL(request.url).pathname.endsWith(
    '/api/v1/auth/refresh',
  )
  if (
    response.status !== 401 ||
    isRefreshRequest ||
    !options.security?.length
  ) {
    return response
  }

  const refreshedSession = await refreshAccessToken()
  if (!refreshedSession) return response

  const headers = new Headers(request.headers)
  headers.set('Authorization', `Bearer ${refreshedSession.accessToken}`)
  const retryFetch = options.fetch ?? globalThis.fetch
  return retryFetch(new Request(request, { headers }))
})
