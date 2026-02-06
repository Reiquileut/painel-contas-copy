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
    expect(get).toHaveBeenCalledWith('/api/admin/accounts', { params: { status: 'approved', search: 'ana' } })

    get.mockResolvedValueOnce({ data: [] })
    await getAccounts()
    expect(get).toHaveBeenCalledWith('/api/admin/accounts', { params: {} })
  })

  it('account CRUD endpoints return payload', async () => {
    const { getAccount, createAccount, updateAccount, updateAccountStatus, deleteAccount } = await import('./accounts')
    get.mockResolvedValueOnce({ data: { id: 2 } })
    post.mockResolvedValueOnce({ data: { id: 3 } })
    put.mockResolvedValueOnce({ data: { id: 4 } })
    patch.mockResolvedValueOnce({ data: { id: 5, status: 'approved' } })
    del.mockResolvedValueOnce({})

    await expect(getAccount(2)).resolves.toEqual({ id: 2 })
    await expect(createAccount({ account_number: '1' } as any)).resolves.toEqual({ id: 3 })
    await expect(updateAccount(4, { buyer_name: 'x' })).resolves.toEqual({ id: 4 })
    await expect(updateAccountStatus(5, 'approved')).resolves.toEqual({ id: 5, status: 'approved' })
    await expect(deleteAccount(6)).resolves.toBeUndefined()

    expect(get).toHaveBeenCalledWith('/api/admin/accounts/2')
    expect(post).toHaveBeenCalledWith('/api/admin/accounts', { account_number: '1' })
    expect(put).toHaveBeenCalledWith('/api/admin/accounts/4', { buyer_name: 'x' })
    expect(patch).toHaveBeenCalledWith('/api/admin/accounts/5/status', { status: 'approved' })
    expect(del).toHaveBeenCalledWith('/api/admin/accounts/6')
  })

  it('stats endpoints return payload', async () => {
    const { getAdminStats, getPublicStats } = await import('./accounts')
    get.mockResolvedValueOnce({ data: { total_accounts: 1 } })
    get.mockResolvedValueOnce({ data: { total_accounts: 2 } })
    await expect(getAdminStats()).resolves.toEqual({ total_accounts: 1 })
    await expect(getPublicStats()).resolves.toEqual({ total_accounts: 2 })
    expect(get).toHaveBeenCalledWith('/api/admin/stats')
    expect(get).toHaveBeenCalledWith('/api/public/stats')
  })
})
