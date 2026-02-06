import { describe, expect, it, vi } from 'vitest'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const patch = vi.fn()
const del = vi.fn()

vi.mock('./client', () => ({
  default: { get, post, put, patch, delete: del },
}))

describe('api/accounts', () => {
  it('getAccounts sends optional params', async () => {
    get.mockResolvedValueOnce({ data: [] })
    const { getAccounts } = await import('./accounts')
    await getAccounts('approved', 'ana')
    expect(get).toHaveBeenCalledWith('/api/v2/admin/accounts', { params: { status: 'approved', search: 'ana' } })

    get.mockResolvedValueOnce({ data: [] })
    await getAccounts()
    expect(get).toHaveBeenCalledWith('/api/v2/admin/accounts', { params: {} })
  })

  it('account CRUD endpoints return payload', async () => {
    const {
      getAccount,
      createAccount,
      updateAccount,
      updateAccountStatus,
      deleteAccount,
      revealAccountPassword,
      rotateAccountPassword,
    } = await import('./accounts')
    get.mockResolvedValueOnce({ data: { id: 2 } })
    post.mockResolvedValueOnce({ data: { id: 3 } })
    put.mockResolvedValueOnce({ data: { id: 4 } })
    patch.mockResolvedValueOnce({ data: { id: 5, status: 'approved' } })
    post.mockResolvedValueOnce({ data: { account_password: 'secret', expires_in_seconds: 30 } })
    post.mockResolvedValueOnce({ data: { id: 7 } })
    del.mockResolvedValueOnce({})

    await expect(getAccount(2)).resolves.toEqual({ id: 2 })
    await expect(createAccount({ account_number: '1' } as any)).resolves.toEqual({ id: 3 })
    await expect(updateAccount(4, { buyer_name: 'x' })).resolves.toEqual({ id: 4 })
    await expect(updateAccountStatus(5, 'approved')).resolves.toEqual({ id: 5, status: 'approved' })
    await expect(revealAccountPassword(7, 'admin-pass')).resolves.toEqual({
      account_password: 'secret',
      expires_in_seconds: 30,
    })
    await expect(rotateAccountPassword(7, 'new-pass')).resolves.toEqual({ id: 7 })
    await expect(deleteAccount(6)).resolves.toBeUndefined()

    expect(get).toHaveBeenCalledWith('/api/v2/admin/accounts/2')
    expect(post).toHaveBeenCalledWith('/api/v2/admin/accounts', { account_number: '1' })
    expect(put).toHaveBeenCalledWith('/api/v2/admin/accounts/4', { buyer_name: 'x' })
    expect(patch).toHaveBeenCalledWith('/api/v2/admin/accounts/5/status', { status: 'approved' })
    expect(post).toHaveBeenCalledWith('/api/v2/admin/accounts/7/password/reveal', { admin_password: 'admin-pass' })
    expect(post).toHaveBeenCalledWith('/api/v2/admin/accounts/7/password/rotate', { new_password: 'new-pass' })
    expect(del).toHaveBeenCalledWith('/api/v2/admin/accounts/6')
  })

  it('stats endpoints return payload', async () => {
    const { getAdminStats, getPublicStats } = await import('./accounts')
    get.mockResolvedValueOnce({ data: { total_accounts: 1 } })
    get.mockResolvedValueOnce({ data: { total_accounts: 2 } })
    await expect(getAdminStats()).resolves.toEqual({ total_accounts: 1 })
    await expect(getPublicStats()).resolves.toEqual({ total_accounts: 2 })
    expect(get).toHaveBeenCalledWith('/api/v2/admin/stats')
    expect(get).toHaveBeenCalledWith('/api/public/stats')
  })
})
