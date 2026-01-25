import client from './client'
import type { LoginCredentials, AuthToken, User } from '../types/auth'

export async function login(credentials: LoginCredentials): Promise<AuthToken> {
  const response = await client.post<AuthToken>('/api/auth/login', credentials)
  return response.data
}

export async function getCurrentUser(): Promise<User> {
  const response = await client.get<User>('/api/auth/me')
  return response.data
}

export async function logout(): Promise<void> {
  await client.post('/api/auth/logout')
}
