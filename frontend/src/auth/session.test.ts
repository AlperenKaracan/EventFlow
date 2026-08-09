import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LoginResponse, UserResponse } from '../api/generated'

type RequestOptions = { security?: ReadonlyArray<unknown> }
type ResponseOptions = RequestOptions & { fetch?: typeof fetch }
type RequestInterceptor = (
  request: Request,
  options: RequestOptions,
) => Request | Promise<Request>
type ResponseInterceptor = (
  response: Response,
  request: Request,
  options: ResponseOptions,
) => Response | Promise<Response>

const mocks = vi.hoisted(() => ({
  loginUser: vi.fn(),
  logoutUser: vi.fn(),
  refreshSession: vi.fn(),
  registerUser: vi.fn(),
  requestInterceptors: [] as Array<RequestInterceptor>,
  responseInterceptors: [] as Array<ResponseInterceptor>,
}))

vi.mock('../api/generated', () => ({
  loginUser: mocks.loginUser,
  logoutUser: mocks.logoutUser,
  refreshSession: mocks.refreshSession,
  registerUser: mocks.registerUser,
}))

vi.mock('../api/client', () => ({
  client: {
    interceptors: {
      request: {
        use: (interceptor: RequestInterceptor) => {
          mocks.requestInterceptors.push(interceptor)
          return 0
        },
      },
      response: {
        use: (interceptor: ResponseInterceptor) => {
          mocks.responseInterceptors.push(interceptor)
          return 0
        },
      },
    },
  },
}))

import {
  clearSession,
  getAccessToken,
  getSessionSnapshot,
  login,
  refreshAccessToken,
} from './session'

const user: UserResponse = {
  id: 'user-1',
  email: 'attendee@example.com',
  fullName: 'Test Katılımcı',
  role: 'attendee',
}

function session(accessToken: string): LoginResponse {
  return { accessToken, expiresIn: 900, tokenType: 'bearer', user }
}

describe('auth session', () => {
  beforeEach(() => {
    clearSession()
    mocks.loginUser.mockReset()
    mocks.logoutUser.mockReset()
    mocks.refreshSession.mockReset()
    mocks.registerUser.mockReset()
  })

  it('keeps the access token in memory and attaches it only to protected requests', async () => {
    const storageSpy = vi.spyOn(Storage.prototype, 'setItem')
    mocks.loginUser.mockResolvedValue({ data: session('memory-token') })

    await login({ email: user.email, password: 'strong-password' })

    const interceptor = mocks.requestInterceptors[0]
    const publicRequest = await interceptor(
      new Request('http://eventflow.test/api/v1/events'),
      {},
    )
    const protectedRequest = await interceptor(
      new Request('http://eventflow.test/api/v1/auth/me'),
      { security: [{}] },
    )

    expect(getAccessToken()).toBe('memory-token')
    expect(publicRequest.headers.has('Authorization')).toBe(false)
    expect(protectedRequest.headers.get('Authorization')).toBe(
      'Bearer memory-token',
    )
    expect(storageSpy).not.toHaveBeenCalled()
    storageSpy.mockRestore()
  })

  it('uses one refresh for concurrent protected 401 responses and retries both requests', async () => {
    mocks.loginUser.mockResolvedValue({ data: session('expired-token') })
    await login({ email: user.email, password: 'strong-password' })

    let resolveRefresh!: (result: { data: LoginResponse }) => void
    mocks.refreshSession.mockReturnValue(
      new Promise((resolve) => {
        resolveRefresh = resolve
      }),
    )
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response(null, { status: 204 }))
    const interceptor = mocks.responseInterceptors[0]
    const options = { security: [{}], fetch: fetchMock }
    const requestOne = new Request(
      'http://eventflow.test/api/v1/me/reservations',
    )
    const requestTwo = new Request('http://eventflow.test/api/v1/auth/me')

    const retryOne = interceptor(
      new Response(null, { status: 401 }),
      requestOne,
      options,
    )
    const retryTwo = interceptor(
      new Response(null, { status: 401 }),
      requestTwo,
      options,
    )

    expect(mocks.refreshSession).toHaveBeenCalledTimes(1)
    resolveRefresh({ data: session('refreshed-token') })
    await Promise.all([retryOne, retryTwo])

    expect(fetchMock).toHaveBeenCalledTimes(2)
    for (const [request] of fetchMock.mock.calls) {
      expect(request).toBeInstanceOf(Request)
      if (!(request instanceof Request))
        throw new Error('Retry request bekleniyordu.')
      expect(request.headers.get('Authorization')).toBe(
        'Bearer refreshed-token',
      )
    }
  })

  it('returns anonymous state when refresh fails', async () => {
    mocks.refreshSession.mockRejectedValue(new Error('invalid refresh'))

    await expect(refreshAccessToken()).resolves.toBeNull()

    expect(getSessionSnapshot()).toEqual({ status: 'anonymous', user: null })
    expect(getAccessToken()).toBeNull()
  })
})
