import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

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

  it('renders empty state', () => {
    render(
      <AccountTable
        accounts={[]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onStatusChange={vi.fn()}
      />
    )
    expect(screen.getByText('Nenhuma conta encontrada')).toBeInTheDocument()
  })

  it('handles table actions and status rendering branches', async () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    const onStatusChange = vi.fn()

    const second = {
      ...mockAccount,
      id: 2,
      account_number: 'ACC-2',
      account_password: 'pwd2',
      purchase_price: null,
      margin_size: null,
      phase1_status: null,
      phase2_status: null,
    }

    const third = { ...mockAccount, id: 3, phase1_status: 'not_started', phase2_status: 'in_progress' }
    const fourth = { ...mockAccount, id: 4, phase1_status: 'passed', phase2_status: 'failed' }
    const fifth = {
      ...mockAccount,
      id: 5,
      margin_size: 1000,
      phase1_status: undefined,
      phase2_status: undefined,
    }

    const confirmSpy = vi.spyOn(window, 'confirm')
    confirmSpy.mockReturnValueOnce(false).mockReturnValueOnce(true)

    render(
      <AccountTable
        accounts={[mockAccount, second, third, fourth, fifth]}
        onEdit={onEdit}
        onDelete={onDelete}
        onStatusChange={onStatusChange}
      />
    )

    const user = userEvent.setup()

    expect(screen.getAllByText('••••••••').length).toBeGreaterThan(0)
    const toggleButton = screen.getAllByRole('button').find((btn) => !btn.getAttribute('title'))!
    await user.click(toggleButton)
    expect(screen.getByText('secret')).toBeInTheDocument()
    await user.click(toggleButton)
    expect(screen.getAllByText('••••••••').length).toBeGreaterThan(0)

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

    expect(screen.getByText('F1: Em Andamento ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Nao Iniciada ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: Nao Iniciada ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Em Andamento ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: Aprovada ($500)')).toBeInTheDocument()
    expect(screen.getByText('F2: Reprovada ($300)')).toBeInTheDocument()
    expect(screen.getByText('F1: - ($500)')).toBeInTheDocument()
    expect(screen.getAllByText('-').length).toBeGreaterThan(0)
  })
})
