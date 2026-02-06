import { useState } from 'react'
import { Edit, Trash2, Copy, KeyRound, ShieldCheck } from 'lucide-react'
import { format } from 'date-fns'
import type { Account, AccountStatus, PhaseStatus } from '../../types/account'

interface AccountTableProps {
  accounts: Account[]
  onEdit: (account: Account) => void
  onDelete: (id: number) => void
  onStatusChange: (id: number, status: AccountStatus) => void
  onRevealPassword: (id: number, adminPassword: string) => Promise<{
    account_password: string
    expires_in_seconds: number
  }>
  onRotatePassword: (id: number, newPassword: string) => Promise<void>
}

export function AccountTable({
  accounts,
  onEdit,
  onDelete,
  onStatusChange,
  onRevealPassword,
  onRotatePassword,
}: AccountTableProps) {
  const [revealedPasswords, setRevealedPasswords] = useState<Record<number, string>>({})

  const handleRevealPassword = async (id: number) => {
    const adminPassword = prompt('Digite sua senha de admin para revelar a senha da conta:')
    if (!adminPassword) return
    try {
      const response = await onRevealPassword(id, adminPassword)
      setRevealedPasswords((prev) => ({ ...prev, [id]: response.account_password }))
      window.setTimeout(() => {
        setRevealedPasswords((prev) => {
          const next = { ...prev }
          delete next[id]
          return next
        })
      }, response.expires_in_seconds * 1000)
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'Nao foi possivel revelar a senha'
      alert(message)
    }
  }

  const handleRotatePassword = async (id: number) => {
    const newPassword = prompt('Digite a nova senha da conta (minimo 8 caracteres):')
    if (!newPassword) return
    if (newPassword.length < 8) {
      alert('A nova senha precisa ter pelo menos 8 caracteres.')
      return
    }
    try {
      await onRotatePassword(id, newPassword)
      setRevealedPasswords((prev) => {
        const next = { ...prev }
        delete next[id]
        return next
      })
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'Nao foi possivel rotacionar a senha'
      alert(message)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const getPhaseLabel = (status: PhaseStatus | null | undefined): string => {
    switch (status) {
      case 'not_started': return 'Nao Iniciada'
      case 'in_progress': return 'Em Andamento'
      case 'passed': return 'Aprovada'
      case 'failed': return 'Reprovada'
      default: return '-'
    }
  }

  const getPhaseColor = (status: PhaseStatus | null | undefined): string => {
    switch (status) {
      case 'not_started': return 'text-gray-500'
      case 'in_progress': return 'text-blue-600'
      case 'passed': return 'text-green-600'
      case 'failed': return 'text-red-600'
      default: return 'text-gray-400'
    }
  }

  const statusOptions: AccountStatus[] = ['pending', 'approved', 'in_copy', 'expired', 'suspended']

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Nenhuma conta encontrada
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Conta
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Servidor
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Comprador
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Compra
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Copies
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Mesa Prop
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Acoes
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {accounts.map((account) => (
            <tr key={account.id} className="hover:bg-gray-50">
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">
                    {account.account_number}
                  </span>
                  <button
                    onClick={() => copyToClipboard(account.account_number)}
                    className="text-gray-400 hover:text-gray-600"
                    title="Copiar"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                {account.server}
                {revealedPasswords[account.id] && (
                  <div className="mt-1 flex items-center gap-2 text-xs text-amber-700">
                    <span className="font-mono">{revealedPasswords[account.id]}</span>
                    <button
                      onClick={() => copyToClipboard(revealedPasswords[account.id])}
                      className="text-amber-600 hover:text-amber-800"
                      title="Copiar senha revelada"
                    >
                      <Copy className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </td>
              <td className="px-4 py-4">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">{account.buyer_name}</p>
                  {account.buyer_email && (
                    <p className="text-gray-500">{account.buyer_email}</p>
                  )}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                {format(new Date(account.purchase_date), 'dd/MM/yyyy')}
                {account.purchase_price && (
                  <p className="text-green-600 font-medium">
                    R$ {Number(account.purchase_price).toFixed(2)}
                  </p>
                )}
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <select
                  value={account.status}
                  onChange={(e) => onStatusChange(account.id, e.target.value as AccountStatus)}
                  className="text-sm border border-gray-200 rounded px-2 py-1"
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status === 'pending' && 'Pendente'}
                      {status === 'approved' && 'Aprovada'}
                      {status === 'in_copy' && 'Em Copy'}
                      {status === 'expired' && 'Expirada'}
                      {status === 'suspended' && 'Suspensa'}
                    </option>
                  ))}
                </select>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm">
                <span className="text-gray-900">{account.copy_count}</span>
                <span className="text-gray-400"> / {account.max_copies}</span>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm">
                {account.margin_size ? (
                  <div className="space-y-1">
                    <p className="font-medium text-gray-900">
                      ${Number(account.margin_size).toLocaleString()}
                    </p>
                    <p className={getPhaseColor(account.phase1_status)}>
                      F1: {getPhaseLabel(account.phase1_status)}
                      {account.phase1_target && ` ($${Number(account.phase1_target).toLocaleString()})`}
                    </p>
                    {account.phase2_status && (
                      <p className={getPhaseColor(account.phase2_status)}>
                        F2: {getPhaseLabel(account.phase2_status)}
                        {account.phase2_target && ` ($${Number(account.phase2_target).toLocaleString()})`}
                      </p>
                    )}
                  </div>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onEdit(account)}
                    className="text-blue-600 hover:text-blue-800"
                    title="Editar"
                  >
                    <Edit className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleRevealPassword(account.id)}
                    className="text-amber-600 hover:text-amber-800"
                    title="Revelar Senha"
                  >
                    <ShieldCheck className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleRotatePassword(account.id)}
                    className="text-emerald-600 hover:text-emerald-800"
                    title="Rotacionar Senha"
                  >
                    <KeyRound className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Tem certeza que deseja excluir esta conta?')) {
                        onDelete(account.id)
                      }
                    }}
                    className="text-red-600 hover:text-red-800"
                    title="Excluir"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
