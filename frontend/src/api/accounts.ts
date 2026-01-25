import client from './client'
import type { Account, AccountCreate, AccountUpdate, Stats, AdminStats } from '../types/account'

// Admin endpoints
export async function getAccounts(status?: string): Promise<Account[]> {
  const params = status ? { status } : {}
  const response = await client.get<Account[]>('/api/admin/accounts', { params })
  return response.data
}

export async function getAccount(id: number): Promise<Account> {
  const response = await client.get<Account>(`/api/admin/accounts/${id}`)
  return response.data
}

export async function createAccount(data: AccountCreate): Promise<Account> {
  const response = await client.post<Account>('/api/admin/accounts', data)
  return response.data
}

export async function updateAccount(id: number, data: AccountUpdate): Promise<Account> {
  const response = await client.put<Account>(`/api/admin/accounts/${id}`, data)
  return response.data
}

export async function updateAccountStatus(id: number, status: string): Promise<Account> {
  const response = await client.patch<Account>(`/api/admin/accounts/${id}/status`, { status })
  return response.data
}

export async function deleteAccount(id: number): Promise<void> {
  await client.delete(`/api/admin/accounts/${id}`)
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await client.get<AdminStats>('/api/admin/stats')
  return response.data
}

// Public endpoints
export async function getPublicStats(): Promise<Stats> {
  const response = await client.get<Stats>('/api/public/stats')
  return response.data
}
