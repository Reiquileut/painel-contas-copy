import { useQuery } from '@tanstack/react-query'
import { Clock, CheckCircle, Copy, XCircle, AlertCircle, Users } from 'lucide-react'
import { getPublicStats } from '../api/accounts'
import { Loading } from '../components/common/Loading'

export function PublicDashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['publicStats'],
    queryFn: getPublicStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) return <Loading />

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-600">Erro ao carregar estatisticas</p>
      </div>
    )
  }

  const statCards = [
    {
      label: 'Total de Contas',
      value: stats?.total_accounts || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      label: 'Pendentes',
      value: stats?.pending || 0,
      icon: Clock,
      color: 'bg-yellow-500',
    },
    {
      label: 'Aprovadas',
      value: stats?.approved || 0,
      icon: CheckCircle,
      color: 'bg-green-500',
    },
    {
      label: 'Em Copy',
      value: stats?.in_copy || 0,
      icon: Copy,
      color: 'bg-indigo-500',
    },
    {
      label: 'Expiradas',
      value: stats?.expired || 0,
      icon: XCircle,
      color: 'bg-gray-500',
    },
    {
      label: 'Suspensas',
      value: stats?.suspended || 0,
      icon: AlertCircle,
      color: 'bg-red-500',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Publico</h1>
        <p className="mt-1 text-sm text-gray-600">
          Estatisticas gerais das contas de copy trade
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat) => (
          <div key={stat.label} className="card">
            <div className="flex items-center gap-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Sobre o Copy Trade</h2>
        <p className="text-gray-600">
          Acompanhe em tempo real as estatisticas das contas de copy trade.
          Os dados sao atualizados automaticamente a cada 30 segundos.
        </p>
      </div>
    </div>
  )
}
