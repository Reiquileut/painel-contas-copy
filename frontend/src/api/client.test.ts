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
    localStorage.clear()
    delete (window as any).__ENV__
  })

  it('prefers API URL from window __ENV__', async () => {
    ;(window as any).__ENV__ = { VITE_API_URL: 'http://custom-api' }
    await import('./client')
    expect(createMock).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://custom-api' })
    )
  })

  it('registers request/response interceptors and adds auth header', async () => {
    localStorage.setItem('token', 'abc123')
    await import('./client')

    expect(requestUse).toHaveBeenCalledTimes(1)
    const requestInterceptor = requestUse.mock.calls[0][0] as (cfg: any) => any
    const cfg = requestInterceptor({ headers: {} })
    expect(cfg.headers.Authorization).toBe('Bearer abc123')

    expect(responseUse).toHaveBeenCalledTimes(1)
    const onSuccess = responseUse.mock.calls[0][0] as (r: any) => any
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>
    expect(onSuccess({ ok: true })).toEqual({ ok: true })

    await expect(onError({ response: { status: 500 } })).rejects.toEqual({ response: { status: 500 } })
    expect(localStorage.getItem('token')).toBe('abc123')
  })

  it('clears token and redirects on 401', async () => {
    localStorage.setItem('token', 'abc123')
    await import('./client')
    const onError = responseUse.mock.calls[0][1] as (e: any) => Promise<any>

    await expect(onError({ response: { status: 401 } })).rejects.toEqual({ response: { status: 401 } })
    expect(localStorage.getItem('token')).toBeNull()
  })
})
