import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import type { User, LoginCredentials } from '../types/auth'
import * as authApi from '../api/auth'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    let isMounted = true
    async function bootstrapSession() {
      try {
        await authApi.refresh()
      } catch {
        // Ignore refresh errors at bootstrap; /me below confirms auth state.
      }

      try {
        const currentUser = await authApi.getCurrentUser()
        if (isMounted) setUser(currentUser)
      } catch {
        if (isMounted) setUser(null)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void bootstrapSession()
    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    if (!user) return
    const refreshInterval = window.setInterval(() => {
      authApi.refresh().catch(() => {
        setUser(null)
        navigate('/login')
      })
    }, 10 * 60 * 1000)
    return () => window.clearInterval(refreshInterval)
  }, [user, navigate])

  const login = async (credentials: LoginCredentials) => {
    const session = await authApi.login(credentials)
    setUser(session.user)
    navigate('/admin')
  }

  const logout = () => {
    void authApi.logout().finally(() => {
      setUser(null)
      navigate('/login')
    })
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
