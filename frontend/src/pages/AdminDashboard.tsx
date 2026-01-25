import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, DollarSign, Calendar, TrendingUp, Users } from 'lucide-react'
import {
  getAccounts,
  createAccount,
  updateAccount,
  updateAccountStatus,
  deleteAccount,
  getAdminStats,
} from '../api/accounts'
import { Loading } from '../components/common/Loading'
import { AccountTable } from '../components/admin/AccountTable'
import { AccountForm } from '../components/admin/AccountForm'
import type { Account, AccountCreate, AccountStatus } from '../types/account'

export function AdminDashboard() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')

  // Queries
  const { data: accounts, isLoading: loadingAccounts } = useQuery({
    queryKey: ['accounts', statusFilter],
    queryFn: () => getAccounts(statusFilter || undefined),
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['adminStats'],
    queryFn: getAdminStats,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
      setShowForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AccountCreate }) =>
      updateAccount(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
      setShowForm(false)
      setEditingAccount(null)
    },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateAccountStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
    },
  })

  const handleSubmit = async (data: AccountCreate) => {
    if (editingAccount) {
      await updateMutation.mutateAsync({ id: editingAccount.id, data })
    } else {
      await createMutation.mutateAsync(data)
    }
  }

  const handleEdit = (account: Account) => {
    setEditingAccount(account)
    setShowForm(true)
  }

  const handleStatusChange = (id: number, status: AccountStatus) => {
    statusMutation.mutate({ id, status })
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingAccount(null)
  }

  if (loadingAccounts || loadingStats) return <Loading />

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Painel Admin</h1>
          <p className="mt-1 text-sm text-gray-600">
            Gerencie todas as contas de copy trade
          </p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Nova Conta
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="bg-blue-500 p-3 rounded-lg">
              <Users className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Contas</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.total_accounts || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-4">
            <div className="bg-green-500 p-3 rounded-lg">
              <DollarSign className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Receita Total</p>
              <p className="text-2xl font-bold text-gray-900">
                R$ {Number(stats?.total_revenue || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-4">
            <div className="bg-indigo-500 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Em Copy</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.in_copy || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-4">
            <div className="bg-yellow-500 p-3 rounded-lg">
              <Calendar className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Este Mes</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.accounts_this_month || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Filtrar por status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">Todos</option>
            <option value="pending">Pendentes</option>
            <option value="approved">Aprovadas</option>
            <option value="in_copy">Em Copy</option>
            <option value="expired">Expiradas</option>
            <option value="suspended">Suspensas</option>
          </select>
        </div>
      </div>

      {/* Accounts Table */}
      <div className="card">
        <AccountTable
          accounts={accounts || []}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onStatusChange={handleStatusChange}
        />
      </div>

      {/* Account Form Modal */}
      {showForm && (
        <AccountForm
          account={editingAccount}
          onSubmit={handleSubmit}
          onClose={handleCloseForm}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  )
}
