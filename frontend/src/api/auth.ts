import client from './client'
import type { LoginCredentials, SessionLoginResponse, User } from '../types/auth'

export async function login(credentials: LoginCredentials): Promise<SessionLoginResponse> {
  const response = await client.post<SessionLoginResponse>('/api/v2/auth/login', credentials)
  return response.data
}

export async function getCurrentUser(): Promise<User> {
  const response = await client.get<User>('/api/v2/auth/me')
  return response.data
}

export async function refresh(): Promise<void> {
  await client.post('/api/v2/auth/refresh')
}

export async function logout(): Promise<void> {
  await client.post('/api/v2/auth/logout')
}
