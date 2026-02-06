import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LoginPage } from './LoginPage'

const loginMock = vi.fn()

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ login: loginMock }),
}))

describe('LoginPage', () => {
  it('validates required fields', async () => {
    render(<LoginPage />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /Entrar/i }))
    expect(await screen.findByText('Usuario obrigatorio')).toBeInTheDocument()
    expect(screen.getByText('Senha obrigatoria')).toBeInTheDocument()
  })

  it('submits successfully', async () => {
    loginMock.mockResolvedValueOnce(undefined)
    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Digite seu usuario'), 'admin')
    await user.type(screen.getByPlaceholderText('Digite sua senha'), '123')
    await user.click(screen.getByRole('button', { name: /Entrar/i }))

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith({ username: 'admin', password: '123' }))
  })

  it('shows axios response detail when login fails with response', async () => {
    loginMock.mockRejectedValueOnce({ response: { data: { detail: 'Credenciais invalidas' } } })
    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Digite seu usuario'), 'admin')
    await user.type(screen.getByPlaceholderText('Digite sua senha'), '123')
    await user.click(screen.getByRole('button', { name: /Entrar/i }))

    expect(await screen.findByText('Credenciais invalidas')).toBeInTheDocument()
  })

  it('falls back to generic message when response has no detail', async () => {
    loginMock.mockRejectedValueOnce({ response: { data: {} } })
    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Digite seu usuario'), 'admin')
    await user.type(screen.getByPlaceholderText('Digite sua senha'), '123')
    await user.click(screen.getByRole('button', { name: /Entrar/i }))

    expect(await screen.findByText('Erro ao fazer login')).toBeInTheDocument()
  })

  it('shows fallback error message for non-response errors', async () => {
    loginMock.mockRejectedValueOnce(new Error('Falha geral'))
    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('Digite seu usuario'), 'admin')
    await user.type(screen.getByPlaceholderText('Digite sua senha'), '123')
    await user.click(screen.getByRole('button', { name: /Entrar/i }))

    expect(await screen.findByText('Falha geral')).toBeInTheDocument()
  })
})
