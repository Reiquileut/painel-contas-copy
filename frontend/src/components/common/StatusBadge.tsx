import type { AccountStatus } from '../../types/account'

const statusConfig: Record<AccountStatus, { label: string; className: string }> = {
  pending: {
    label: 'Pendente',
    className: 'bg-yellow-100 text-yellow-800',
  },
  approved: {
    label: 'Aprovada',
    className: 'bg-green-100 text-green-800',
  },
  in_copy: {
    label: 'Em Copy',
    className: 'bg-blue-100 text-blue-800',
  },
  expired: {
    label: 'Expirada',
    className: 'bg-gray-100 text-gray-800',
  },
  suspended: {
    label: 'Suspensa',
    className: 'bg-red-100 text-red-800',
  },
}

interface StatusBadgeProps {
  status: AccountStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status]
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.className}`}>
      {config.label}
    </span>
  )
}
