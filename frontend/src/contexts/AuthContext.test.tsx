import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { mockUser } from '../test/fixtures'

const { navigateMock, loginApi, getCurrentUserApi } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  loginApi: vi.fn(),
  getCurrentUserApi: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => navigateMock }
})

vi.mock('../api/auth', () => ({
  login: loginApi,
  getCurrentUser: getCurrentUserApi,
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
    localStorage.clear()
  })

  it('throws when useAuth is used outside provider', () => {
    const Broken = () => {
      useAuth()
      return null
    }
    expect(() => render(<Broken />)).toThrow('useAuth must be used within an AuthProvider')
  })

  it('loads with no token', async () => {
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(getCurrentUserApi).not.toHaveBeenCalled()
  })

  it('loads authenticated user when token exists', async () => {
    localStorage.setItem('token', 'tkn')
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(screen.getByTestId('auth')).toHaveTextContent('true')
    expect(screen.getByTestId('username')).toHaveTextContent('admin')
  })

  it('removes token when bootstrap getCurrentUser fails', async () => {
    localStorage.setItem('token', 'bad')
    getCurrentUserApi.mockRejectedValueOnce(new Error('bad token'))
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'))
    expect(localStorage.getItem('token')).toBeNull()
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
  })

  it('login stores token, sets user and navigates', async () => {
    loginApi.mockResolvedValueOnce({ access_token: 'new-token' })
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    const user = userEvent.setup()
    renderProvider()
    await user.click(screen.getByText('login'))
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('true'))
    expect(localStorage.getItem('token')).toBe('new-token')
    expect(navigateMock).toHaveBeenCalledWith('/admin')
  })

  it('logout clears user and navigates login', async () => {
    localStorage.setItem('token', 'tkn')
    getCurrentUserApi.mockResolvedValueOnce(mockUser)
    const user = userEvent.setup()
    renderProvider()
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('true'))
    await user.click(screen.getByText('logout'))
    expect(localStorage.getItem('token')).toBeNull()
    expect(screen.getByTestId('auth')).toHaveTextContent('false')
    expect(navigateMock).toHaveBeenCalledWith('/login')
  })
})
