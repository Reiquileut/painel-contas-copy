import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AccountTable } from './AccountTable'
import { mockAccount } from '../../test/fixtures'

const clipboardWriteText = vi.fn()

describe('AccountTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: clipboardWriteText },
      configurable: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders empty state', () => {
    render(
      <AccountTable
        accounts={[]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
        onRevealPassword={vi.fn()}
        onRotatePassword={vi.fn()}
      />
    )
    expect(screen.getByText('Nenhuma conta encontrada')).toBeInTheDocument()
  })

  it('handles table actions and status rendering branches', async () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    const onStatusChange = vi.fn()
    const onRevealPassword = vi.fn().mockResolvedValue({
      account_password: 'revealed-secret',
      expires_in_seconds: 1,
    })
    const onRotatePassword = vi.fn().mockResolvedValue(undefined)
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const promptSpy = vi.spyOn(window, 'prompt')
    const setTimeoutSpy = vi.spyOn(window, 'setTimeout').mockImplementation(((cb: any) => {
      cb()
      return 1 as any
    }) as any)
    promptSpy
      .mockReturnValueOnce('admin-password')
      .mockReturnValueOnce('short')
      .mockReturnValueOnce('valid-new-password')

    const second = {
      ...mockAccount,
      id: 2,
      account_number: 'ACC-2',
      purchase_price: null,
      margin_size: null,
      phase1_status: null,
      phase2_status: null,
    }

    const third = {
      ...mockAccount,
      id: 3,
      phase1_status: 'not_started' as const,
      phase2_status: 'in_progress' as const,
    }
    const fourth = {
      ...mockAccount,
      id: 4,
      phase1_status: 'passed' as const,
      phase2_status: 'failed' as const,
    }
    const fifth = {
      ...mockAccount,
      id: 5,
      margin_size: 1000,
      phase1_status: null,
      phase2_status: null,
    }

    const confirmSpy = vi.spyOn(window, 'confirm')
    confirmSpy.mockReturnValueOnce(false).mockReturnValueOnce(true)

    render(
      <AccountTable
        accounts={[mockAccount, second, third, fourth, fifth]}
        onEdit={onEdit}
        onDelete={onDelete}
        onStatusChange={onStatusChange}
        onRevealPassword={onRevealPassword}
        onRotatePassword={onRotatePassword}
      />
    )

    const user = userEvent.setup()

    fireEvent.click(screen.getAllByTitle('Copiar')[0])

    const selects = screen.getAllByRole('combobox')
    await user.selectOptions(selects[0], 'approved')
    expect(onStatusChange).toHaveBeenCalledWith(1, 'approved')

    await user.click(screen.getAllByTitle('Editar')[0])
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }))

    await user.click(screen.getAllByTitle('Excluir')[0])
    expect(onDelete).not.toHaveBeenCalled()
    await user.click(screen.getAllByTitle('Excluir')[0])
    expect(onDelete).toHaveBeenCalledWith(1)

    await user.click(screen.getAllByTitle('Revelar Senha')[0])
    expect(onRevealPassword).toHaveBeenCalledWith(1, 'admin-password')
    expect(screen.queryByText('revealed-secret')).not.toBeInTheDocument()

    await user.click(screen.getAllByTitle('Rotacionar Senha')[0])
    expect(alertSpy).toHaveBeenCalledWith('A nova senha precisa ter pelo menos 8 caracteres.')

    await user.click(screen.getAllByTitle('Rotacionar Senha')[0])
    expect(onRotatePassword).toHaveBeenCalledWith(1, 'valid-new-password')

    expect(screen.getByText('F1: Em Andamento ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Nao Iniciada ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: Nao Iniciada ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Em Andamento ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: Aprovada ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Reprovada ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: - ($500)')).toBeInTheDocument()
    expect(screen.getAllByText('-').length).toBeGreaterThan(0)

    alertSpy.mockRestore()
    promptSpy.mockRestore()
    setTimeoutSpy.mockRestore()
  })

  it('shows revealed password and allows copying before timeout cleanup', async () => {
    const onRevealPassword = vi.fn().mockResolvedValue({
      account_password: 'revealed-secret',
      expires_in_seconds: 30,
    })
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('admin-password')
    const setTimeoutSpy = vi.spyOn(window, 'setTimeout')

    render(
      <AccountTable
        accounts={[mockAccount]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
        onRevealPassword={onRevealPassword}
        onRotatePassword={vi.fn()}
      />
    )

    const user = userEvent.setup()
    await user.click(screen.getByTitle('Revelar Senha'))

    expect(onRevealPassword).toHaveBeenCalledWith(1, 'admin-password')
    expect(await screen.findByText('revealed-secret')).toBeInTheDocument()
    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 30000)

    expect(screen.getByTitle('Copiar senha revelada')).toBeInTheDocument()

    promptSpy.mockRestore()
    setTimeoutSpy.mockRestore()
  })

  it('shows alerts when reveal or rotate actions fail', async () => {
    const onRevealPassword = vi.fn().mockRejectedValue({
      response: { data: { detail: 'Falha ao revelar senha' } },
    })
    const onRotatePassword = vi.fn().mockRejectedValue(new Error('Falha ao rotacionar senha'))
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const promptSpy = vi.spyOn(window, 'prompt')
    promptSpy.mockReturnValueOnce('admin-password').mockReturnValueOnce('valid-pass-123')

    render(
      <AccountTable
        accounts={[mockAccount]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
        onRevealPassword={onRevealPassword}
        onRotatePassword={onRotatePassword}
      />
    )

    const user = userEvent.setup()
    await user.click(screen.getByTitle('Revelar Senha'))
    expect(alertSpy).toHaveBeenCalledWith('Falha ao revelar senha')

    await user.click(screen.getByTitle('Rotacionar Senha'))
    expect(alertSpy).toHaveBeenCalledWith('Falha ao rotacionar senha')

    alertSpy.mockRestore()
    promptSpy.mockRestore()
  })
})
