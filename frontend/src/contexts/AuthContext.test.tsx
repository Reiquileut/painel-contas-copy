import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { mockUser } from '../test/fixtures'

const { navigateMock, loginApi, getCurrentUserApi, refreshApi, logoutApi } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  loginApi: vi.fn(),
  getCurrentUserApi: vi.fn(),
  refreshApi: vi.fn(),
  logoutApi: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => navigateMock }
})

vi.mock('../api/auth', () => ({
  login: loginApi,
  getCurrentUser: getCurrentUserApi,
  refresh: refreshApi,
  logout: logoutApi,
}))

function Consumer() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="username">{user?.username || ''}</span>
      <button onClick={() => login({ username: 'admin', password: 'pwd' })}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

function renderProvider() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it('throws when useAuth is used outside provider', () => {
    const Broken = () => {
      useAuth()
      return null
    }
    expect(() => render(<Broken />)).toThrow('useAuth must be used within an AuthProvider')
  })

  it('loads unauthenticated when bootstrap fails', async () => {
    refreshApi.mockRejectedValueOnce(new Error('no refresh'))
    getCurrentUserApi.mockRejectedValueOnce(new Error('no session'))
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(refreshApi).toHaveBeenCalled()
    expect(getCurrentUserApi).toHaveBeenCalled()
  })

  it('loads authenticated user and refreshes periodically', async () => {
    let intervalCallback: (() => void) | undefined
    const setIntervalSpy = vi.spyOn(window, 'setInterval').mockImplementation(((cb: any) => {
      intervalCallback = cb
      return 1 as any
    }) as any)
    const clearIntervalSpy = vi.spyOn(window, 'clearInterval').mockImplementation(() => {})

    refreshApi.mockResolvedValue(undefined)
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('auth')).toHaveTextContent('true')
    expect(screen.getByTestId('username')).toHaveTextContent('admin')

    expect(setIntervalSpy).toHaveBeenCalled()
    intervalCallback?.()
    await waitFor(() => expect(refreshApi).toHaveBeenCalledTimes(2))
    clearIntervalSpy.mockRestore()
    setIntervalSpy.mockRestore()
  })

  it('clears user when periodic refresh fails', async () => {
    let intervalCallback: (() => void) | undefined
    const setIntervalSpy = vi.spyOn(window, 'setInterval').mockImplementation(((cb: any) => {
      intervalCallback = cb
      return 1 as any
    }) as any)
    const clearIntervalSpy = vi.spyOn(window, 'clearInterval').mockImplementation(() => {})

    refreshApi.mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error('expired'))
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('true'))
    intervalCallback?.()
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('false'))
    expect(navigateMock).toHaveBeenCalledWith('/login')
    clearIntervalSpy.mockRestore()
    setIntervalSpy.mockRestore()
  })

  it('login sets user and navigates', async () => {
    refreshApi.mockResolvedValueOnce(undefined)
    getCurrentUserApi.mockRejectedValueOnce(new Error('no session'))
    loginApi.mockResolvedValueOnce({ user: mockUser, session_expires_at: '2026-01-01T00:00:00Z' })
    const user = userEvent.setup()
    renderProvider()
    await user.click(screen.getByText('login'))
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('true'))
    expect(navigateMock).toHaveBeenCalledWith('/admin')
  })

  it('logout clears user and navigates login', async () => {
    refreshApi.mockResolvedValueOnce(undefined)
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    logoutApi.mockResolvedValueOnce(undefined)
    const user = userEvent.setup()
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('true'))
    await user.click(screen.getByText('logout'))
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('false'))
    expect(logoutApi).toHaveBeenCalled()
    expect(navigateMock).toHaveBeenCalledWith('/login')
  })
})
