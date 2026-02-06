export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface SessionLoginResponse {
  user: User
  session_expires_at: string
}
