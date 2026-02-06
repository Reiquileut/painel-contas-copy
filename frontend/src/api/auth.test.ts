import { describe, expect, it, vi } from 'vitest'

const post = vi.fn()
const get = vi.fn()

vi.mock('./client', () => ({
  default: { post, get },
}))

describe('api/auth', () => {
  it('login returns payload', async () => {
    const data = { user: { id: 1, username: 'a' }, session_expires_at: '2026-01-01T00:00:00Z' }
    post.mockResolvedValueOnce({ data })
    const { login } = await import('./auth')
    await expect(login({ username: 'a', password: 'b' })).resolves.toEqual(data)
    expect(post).toHaveBeenCalledWith('/api/v2/auth/login', { username: 'a', password: 'b' })
  })

  it('getCurrentUser returns payload', async () => {
    const user = { id: 1, username: 'admin' }
    get.mockResolvedValueOnce({ data: user })
    const { getCurrentUser } = await import('./auth')
    await expect(getCurrentUser()).resolves.toEqual(user)
    expect(get).toHaveBeenCalledWith('/api/v2/auth/me')
  })

  it('refresh posts endpoint', async () => {
    post.mockResolvedValueOnce({})
    const { refresh } = await import('./auth')
    await expect(refresh()).resolves.toBeUndefined()
    expect(post).toHaveBeenCalledWith('/api/v2/auth/refresh')
  })

  it('logout posts endpoint', async () => {
    post.mockResolvedValueOnce({})
    const { logout } = await import('./auth')
    await expect(logout()).resolves.toBeUndefined()
    expect(post).toHaveBeenCalledWith('/api/v2/auth/logout')
  })
})
