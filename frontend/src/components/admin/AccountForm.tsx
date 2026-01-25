import { useForm } from 'react-hook-form'
import { X } from 'lucide-react'
import type { Account, AccountCreate, AccountStatus } from '../../types/account'

interface AccountFormProps {
  account?: Account | null
  onSubmit: (data: AccountCreate) => Promise<void>
  onClose: () => void
  isLoading: boolean
}

export function AccountForm({ account, onSubmit, onClose, isLoading }: AccountFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<AccountCreate>({
    defaultValues: account ? {
      account_number: account.account_number,
      account_password: '',
      server: account.server,
      buyer_name: account.buyer_name,
      buyer_email: account.buyer_email || '',
      buyer_phone: account.buyer_phone || '',
      buyer_notes: account.buyer_notes || '',
      purchase_date: account.purchase_date,
      expiry_date: account.expiry_date || '',
      purchase_price: account.purchase_price || undefined,
      status: account.status,
      max_copies: account.max_copies,
    } : {
      status: 'pending',
      max_copies: 1,
    },
  })

  const statusOptions: { value: AccountStatus; label: string }[] = [
    { value: 'pending', label: 'Pendente' },
    { value: 'approved', label: 'Aprovada' },
    { value: 'in_copy', label: 'Em Copy' },
    { value: 'expired', label: 'Expirada' },
    { value: 'suspended', label: 'Suspensa' },
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {account ? 'Editar Conta' : 'Nova Conta'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Dados da Conta */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Dados da Conta
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Numero da Conta *
                </label>
                <input
                  {...register('account_number', { required: 'Obrigatorio' })}
                  className="input mt-1"
                  placeholder="123456"
                />
                {errors.account_number && (
                  <p className="mt-1 text-sm text-red-600">{errors.account_number.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Senha da Conta {!account && '*'}
                </label>
                <input
                  {...register('account_password', {
                    required: !account ? 'Obrigatorio' : false,
                  })}
                  type="password"
                  className="input mt-1"
                  placeholder={account ? '(manter atual)' : 'Senha'}
                />
                {errors.account_password && (
                  <p className="mt-1 text-sm text-red-600">{errors.account_password.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Servidor *
                </label>
                <input
                  {...register('server', { required: 'Obrigatorio' })}
                  className="input mt-1"
                  placeholder="Exness-MT5"
                />
                {errors.server && (
                  <p className="mt-1 text-sm text-red-600">{errors.server.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Status
                </label>
                <select {...register('status')} className="input mt-1">
                  {statusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Dados do Comprador */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Dados do Comprador
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Nome *
                </label>
                <input
                  {...register('buyer_name', { required: 'Obrigatorio' })}
                  className="input mt-1"
                  placeholder="Nome completo"
                />
                {errors.buyer_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.buyer_name.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <input
                  {...register('buyer_email')}
                  type="email"
                  className="input mt-1"
                  placeholder="email@exemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Telefone
                </label>
                <input
                  {...register('buyer_phone')}
                  className="input mt-1"
                  placeholder="(11) 99999-9999"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Observacoes
              </label>
              <textarea
                {...register('buyer_notes')}
                rows={3}
                className="input mt-1"
                placeholder="Anotacoes sobre o comprador..."
              />
            </div>
          </div>

          {/* Dados da Compra */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Dados da Compra
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Data da Compra *
                </label>
                <input
                  {...register('purchase_date', { required: 'Obrigatorio' })}
                  type="date"
                  className="input mt-1"
                />
                {errors.purchase_date && (
                  <p className="mt-1 text-sm text-red-600">{errors.purchase_date.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Data de Expiracao
                </label>
                <input
                  {...register('expiry_date')}
                  type="date"
                  className="input mt-1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Valor Pago (R$)
                </label>
                <input
                  {...register('purchase_price', { valueAsNumber: true })}
                  type="number"
                  step="0.01"
                  className="input mt-1"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Max. Copies
                </label>
                <input
                  {...register('max_copies', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  className="input mt-1"
                />
              </div>
            </div>
          </div>

          {/* Botoes */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? 'Salvando...' : account ? 'Atualizar' : 'Criar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
