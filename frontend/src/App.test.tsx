import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import App from './App'

const useAuthMock = vi.fn()

vi.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: any }) => <>{children}</>,
  useAuth: () => useAuthMock(),
}))

vi.mock('./components/common/Header', () => ({ Header: () => <div>HeaderMock</div> }))
vi.mock('./components/common/Loading', () => ({ Loading: () => <div>LoadingMock</div> }))
vi.mock('./pages/LoginPage', () => ({ LoginPage: () => <div>LoginMock</div> }))
vi.mock('./pages/PublicDashboard', () => ({ PublicDashboard: () => <div>PublicMock</div> }))
vi.mock('./pages/AdminDashboard', () => ({ AdminDashboard: () => <div>AdminMock</div> }))

function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )
}

describe('App routing', () => {
  it('shows loading route while auth is loading', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: false, isLoading: true })
    renderApp('/admin')
    expect(screen.getByText('LoadingMock')).toBeInTheDocument()
  })

  it('redirects unauthenticated user from /admin to /login', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: false, isLoading: false })
    renderApp('/admin')
    expect(screen.getByText('LoginMock')).toBeInTheDocument()
  })

  it('renders admin for authenticated user and fallback redirect', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: true, isLoading: false })
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByText('AdminMock')).toBeInTheDocument()

    render(
      <MemoryRouter initialEntries={['/desconhecida']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByText('PublicMock')).toBeInTheDocument()
    expect(screen.getAllByText('HeaderMock').length).toBeGreaterThan(0)
  })
})
