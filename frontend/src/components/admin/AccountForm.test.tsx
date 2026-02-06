import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { AccountForm } from './AccountForm'
import { mockAccount } from '../../test/fixtures'

describe('AccountForm', () => {
  it('validates required fields for new account', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(
      <AccountForm
        account={null}
        onSubmit={onSubmit}
        onClose={vi.fn()}
        isLoading={false}
      />
    )

    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Criar' }))

    expect(await screen.findAllByText('Obrigatorio')).toHaveLength(5)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits cleaned payload and supports edit mode', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const user = userEvent.setup()

    const { rerender } = render(
      <AccountForm
        account={null}
        onSubmit={onSubmit}
        onClose={onClose}
        isLoading={false}
      />
    )

    await user.type(screen.getByPlaceholderText('123456'), 'ACC-900')
    await user.type(screen.getByPlaceholderText('Senha'), 'pass-900')
    await user.type(screen.getByPlaceholderText('Exness-MT5'), 'Srv')
    await user.type(screen.getByPlaceholderText('Nome completo'), 'Buyer X')
    const numericInputs = screen.getAllByPlaceholderText('0.00')
    await user.type(numericInputs[0], '150')
    await user.type(numericInputs[1], '12')
    await user.type(numericInputs[2], '13')
    await user.type(numericInputs[3], '14')

    const dateInput = document.querySelector('input[type="date"]') as HTMLInputElement
    await user.type(dateInput, '2026-02-01')

    await user.click(screen.getByRole('button', { name: 'Criar' }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1))
    const payload = onSubmit.mock.calls[0][0]
    expect(payload.account_number).toBe('ACC-900')
    expect(payload.account_password).toBe('pass-900')
    expect(payload.server).toBe('Srv')
    expect(payload.buyer_name).toBe('Buyer X')
    expect(payload.purchase_price).toBe(150)
    expect(payload.margin_size).toBe(12)
    expect(payload.phase1_target).toBe(13)
    expect(payload.phase2_target).toBe(14)
    expect(payload.phase1_status).toBe('not_started')
    expect(payload.phase2_status).toBeUndefined()

    const nullableAccount = {
      ...mockAccount,
      buyer_email: null,
      buyer_phone: null,
      buyer_notes: null,
      expiry_date: null,
      purchase_price: null,
      margin_size: null,
      phase1_target: null,
      phase1_status: null,
      phase2_target: null,
      phase2_status: null,
    }

    rerender(
      <AccountForm
        account={nullableAccount}
        onSubmit={onSubmit}
        onClose={onClose}
        isLoading={false}
      />
    )

    expect(screen.getByText('Editar Conta')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('(manter atual)')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Atualizar' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(onClose).toHaveBeenCalled()

    rerender(
      <AccountForm
        account={nullableAccount}
        onSubmit={onSubmit}
        onClose={onClose}
        isLoading={true}
      />
    )
    expect(screen.getByRole('button', { name: 'Salvando...' })).toBeDisabled()
  })
})
