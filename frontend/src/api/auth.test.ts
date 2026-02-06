import { describe, expect, it, vi } from 'vitest'

const post = vi.fn()
const get = vi.fn()

vi.mock('./client', () => ({
  default: { post, get },
}))

describe('api/auth', () => {
  it('login returns payload', async () => {
    const data = { access_token: 'token', token_type: 'bearer' }
    post.mockResolvedValueOnce({ data })
    const { login } = await import('./auth')
    await expect(login({ username: 'a', password: 'b' })).resolves.toEqual(data)
    expect(post).toHaveBeenCalledWith('/api/auth/login', { username: 'a', password: 'b' })
  })

  it('getCurrentUser returns payload', async () => {
    const user = { id: 1, username: 'admin' }
    get.mockResolvedValueOnce({ data: user })
    const { getCurrentUser } = await import('./auth')
    await expect(getCurrentUser()).resolves.toEqual(user)
    expect(get).toHaveBeenCalledWith('/api/auth/me')
  })

  it('logout posts endpoint', async () => {
    post.mockResolvedValueOnce({})
    const { logout } = await import('./auth')
    await expect(logout()).resolves.toBeUndefined()
    expect(post).toHaveBeenCalledWith('/api/auth/logout')
  })
})
