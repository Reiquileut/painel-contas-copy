import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { Header } from './Header'

const logoutMock = vi.fn()
const useAuthMock = vi.fn()

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => useAuthMock(),
}))

function renderHeader(pathname: string) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <Header />
    </MemoryRouter>
  )
}

describe('Header', () => {
  it('shows login button when unauthenticated', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: false, user: null, logout: logoutMock })
    renderHeader('/')
    expect(screen.getByText('Entrar')).toBeInTheDocument()
    expect(screen.queryByText('Admin')).not.toBeInTheDocument()
  })

  it('shows admin links and logout when authenticated', async () => {
    useAuthMock.mockReturnValue({ isAuthenticated: true, user: { username: 'admin' }, logout: logoutMock })
    const user = userEvent.setup()
    renderHeader('/admin')
    expect(screen.getByText('Admin')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
    await user.click(screen.getByText('Sair'))
    expect(logoutMock).toHaveBeenCalled()
  })

  it('renders admin link as inactive when not on admin route', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: true, user: { username: 'admin' }, logout: logoutMock })
    renderHeader('/')
    const adminLink = screen.getByText('Admin')
    expect(adminLink.className).toContain('text-gray-600')
  })
})
