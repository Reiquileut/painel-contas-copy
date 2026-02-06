import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AdminDashboard } from './AdminDashboard'
import { mockAccount, mockAdminStats } from '../test/fixtures'

const getAccountsApi = vi.fn()
const createAccountApi = vi.fn()
const updateAccountApi = vi.fn()
const updateAccountStatusApi = vi.fn()
const deleteAccountApi = vi.fn()
const getAdminStatsApi = vi.fn()

const invalidateQueries = vi.fn()
const useQueryMock = vi.fn()
const useMutationMock = vi.fn()
const mutationOptions: any[] = []

const behavior = {
  createFail: false,
  updateFail: false,
}

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({ invalidateQueries }),
  useQuery: (args: any) => useQueryMock(args),
  useMutation: (options: any) => {
    mutationOptions.push(options)
    return useMutationMock(options)
  },
}))

vi.mock('../api/accounts', () => ({
  getAccounts: (...args: any[]) => getAccountsApi(...args),
  createAccount: (...args: any[]) => createAccountApi(...args),
  updateAccount: (...args: any[]) => updateAccountApi(...args),
  updateAccountStatus: (...args: any[]) => updateAccountStatusApi(...args),
  deleteAccount: (...args: any[]) => deleteAccountApi(...args),
  getAdminStats: (...args: any[]) => getAdminStatsApi(...args),
}))

vi.mock('../components/common/Loading', () => ({ Loading: () => <div>LoadingMock</div> }))
vi.mock('../components/admin/AccountTable', () => ({
  AccountTable: ({ onEdit, onDelete, onStatusChange }: any) => (
    <div>
      <button onClick={() => onEdit(mockAccount)}>edit</button>
      <button onClick={() => onDelete(99)}>delete</button>
      <button onClick={() => onStatusChange(77, 'approved')}>status</button>
    </div>
  ),
}))
vi.mock('../components/admin/AccountForm', () => ({
  AccountForm: ({ onSubmit, onClose, isLoading }: any) => (
    <div>
      <span>{isLoading ? 'form-loading' : 'form-idle'}</span>
      <button onClick={() => onSubmit({ account_number: 'A-1' })}>submit-form</button>
      <button onClick={onClose}>close-form</button>
    </div>
  ),
}))

describe('AdminDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mutationOptions.length = 0
    behavior.createFail = false
    behavior.updateFail = false

    useQueryMock.mockImplementation(({ queryKey }: any) => {
      if (queryKey[0] === 'accounts') {
        return { data: [mockAccount], isLoading: false }
      }
      return { data: mockAdminStats, isLoading: false }
    })

    let call = 0
    createAccountApi.mockResolvedValue({})
    updateAccountApi.mockResolvedValue({})
    updateAccountStatusApi.mockResolvedValue({})
    deleteAccountApi.mockResolvedValue({})
    const createMutationObj = {
      isPending: false,
      mutateAsync: vi.fn(async () => {
        if (behavior.createFail) {
          throw { response: { data: { detail: 'Erro create' } } }
        }
      }),
    }
    const updateMutationObj = {
      isPending: false,
      mutateAsync: vi.fn(async () => {
        if (behavior.updateFail) {
          throw new Error('Erro update')
        }
      }),
    }
    const statusMutationObj = { mutate: vi.fn() }
    const deleteMutationObj = { mutate: vi.fn() }
    const ordered = [createMutationObj, updateMutationObj, statusMutationObj, deleteMutationObj]
    useMutationMock.mockImplementation(() => {
      const idx = call % 4
      call += 1
      return ordered[idx]
    })

    vi.spyOn(window, 'alert').mockImplementation(() => {})
  })

  it('shows loading state when any query is loading', () => {
    useQueryMock.mockImplementationOnce(() => ({ data: undefined, isLoading: true }))
    useQueryMock.mockImplementationOnce(() => ({ data: undefined, isLoading: false }))
    render(<AdminDashboard />)
    expect(screen.getByText('LoadingMock')).toBeInTheDocument()
  })

  it('handles flows, debounce fields and mutation callbacks', async () => {
    const user = userEvent.setup()
    render(<AdminDashboard />)

    expect(screen.getByText('Painel Admin')).toBeInTheDocument()
    expect(screen.getByText('R$ 999.99')).toBeInTheDocument()

    await user.selectOptions(screen.getByDisplayValue('Todos'), 'approved')
    await user.type(screen.getByPlaceholderText('Nome do comprador...'), 'ana')

    await user.click(screen.getByRole('button', { name: /Nova Conta/i }))
    expect(screen.getByText('form-idle')).toBeInTheDocument()

    await user.click(screen.getByText('submit-form'))
    await user.click(screen.getByText('close-form'))

    await user.click(screen.getByText('edit'))
    await user.click(screen.getByText('submit-form'))

    await user.click(screen.getByText('status'))
    await user.click(screen.getByText('delete'))

    mutationOptions[0].onSuccess?.()
    mutationOptions[1].onSuccess?.()
    await mutationOptions[1].mutationFn({ id: 1, data: { buyer_name: 'x' } })
    await mutationOptions[2].mutationFn({ id: 2, status: 'approved' })
    mutationOptions[2].onSuccess?.()
    mutationOptions[3].onSuccess?.()

    await waitFor(() => expect(invalidateQueries).toHaveBeenCalled())

    mutationOptions[0].onError?.({ response: { data: { detail: 'Erro create' } } })
    mutationOptions[1].onError?.(new Error('Erro update'))

    behavior.createFail = true
    await user.click(screen.getByRole('button', { name: /Nova Conta/i }))
    await user.click(screen.getByText('submit-form'))

    behavior.updateFail = true
    await user.click(screen.getByText('edit'))
    await user.click(screen.getByText('submit-form'))

    expect(window.alert).toHaveBeenCalled()
    expect(updateAccountApi).toHaveBeenCalledWith(1, { buyer_name: 'x' })
    expect(updateAccountStatusApi).toHaveBeenCalledWith(2, 'approved')
  })
})
