import { beforeEach, describe, expect, it, vi } from 'vitest'

const requestUse = vi.fn()
const responseUse = vi.fn()
const createMock = vi.fn()
const mockClient = {
  interceptors: {
    request: { use: requestUse },
    response: { use: responseUse },
  },
}

vi.mock('axios', () => ({
  default: {
    create: createMock.mockReturnValue(mockClient),
  },
}))

describe('api/client', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    delete (window as any).__ENV__
    document.cookie = 'ct_csrf=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
  })

  it('prefers API URL from window __ENV__', async () => {
    ;(window as any).__ENV__ = { VITE_API_URL: 'http://custom-api' }
    await import('./client')
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://custom-api' })
    )
  })

  it('registers request/response interceptors and adds csrf header on unsafe methods', async () => {
    document.cookie = 'ct_csrf=csrf-token-value'
    await import('./client')

    expect(requestUse).toHaveBeenCalledTimes(1)
    const requestInterceptor = requestUse.mock.calls[0][0] as (cfg: any) => any
    const postConfig = requestInterceptor({ method: 'post', headers: {} })
    expect(postConfig.headers['X-CSRF-Token']).toBe('csrf-token-value')

    const getConfig = requestInterceptor({ method: 'get', headers: {} })
    expect(getConfig.headers['X-CSRF-Token']).toBeUndefined()

    expect(responseUse).toHaveBeenCalledTimes(1)
    const onSuccess = responseUse.mock.calls[0][0] as (r: any) => any
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>
    expect(onSuccess({ ok: true })).toEqual({ ok: true })

    await expect(onError({ response: { status: 500 } })).rejects.toEqual({ response: { status: 500 } })
  })

  it('redirects on 401 from protected endpoints when not on login page', async () => {
    const originalLocation = window.location
    delete (window as any).location
    ;(window as any).location = { href: '/admin', pathname: '/admin' }

    await import('./client')
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>

    await expect(
      onError({ response: { status: 401 }, config: { url: '/api/v2/admin/accounts' } })
    ).rejects.toEqual({ response: { status: 401 }, config: { url: '/api/v2/admin/accounts' } })
    expect((window as any).location.href).toBe('/login')

    ;(window as any).location = originalLocation
  })

  it('does not redirect on 401 from auth endpoints', async () => {
    const originalLocation = window.location
    delete (window as any).location
    ;(window as any).location = { href: '/', pathname: '/' }

    await import('./client')
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>

    await expect(
      onError({ response: { status: 401 }, config: { url: '/api/v2/auth/me' } })
    ).rejects.toEqual({ response: { status: 401 }, config: { url: '/api/v2/auth/me' } })
    expect((window as any).location.href).toBe('/')

    ;(window as any).location = originalLocation
  })

  it('does not redirect on 401 when already on login page', async () => {
    const originalLocation = window.location
    delete (window as any).location
    ;(window as any).location = { href: '/login', pathname: '/login' }

    await import('./client')
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>

    await expect(
      onError({ response: { status: 401 }, config: { url: '/api/v2/admin/accounts' } })
    ).rejects.toEqual({ response: { status: 401 }, config: { url: '/api/v2/admin/accounts' } })
    expect((window as any).location.href).toBe('/login')

    ;(window as any).location = originalLocation
  })
})
