import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PublicDashboard } from './PublicDashboard'

const useQueryMock = vi.fn()

vi.mock('@tanstack/react-query', () => ({
  useQuery: (args: any) => useQueryMock(args),
}))

describe('PublicDashboard', () => {
  it('renders loading state', () => {
    useQueryMock.mockReturnValue({ isLoading: true, error: null, data: null })
    const { container } = render(<PublicDashboard />)
    expect(container.querySelector('.animate-spin')).toBeTruthy()
  })

  it('renders error state', () => {
    useQueryMock.mockReturnValue({ isLoading: false, error: new Error('x'), data: null })
    render(<PublicDashboard />)
    expect(screen.getByText('Erro ao carregar estatisticas')).toBeInTheDocument()
  })

  it('renders stats cards with defaults', () => {
    useQueryMock.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        total_accounts: 1,
        pending: 2,
        approved: 3,
        in_copy: 4,
        expired: 5,
        suspended: 6,
      },
    })
    render(<PublicDashboard />)
    expect(screen.getByText('Dashboard Publico')).toBeInTheDocument()
    expect(screen.getByText('Total de Contas')).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
  })

  it('renders zero values when stats are missing', () => {
    useQueryMock.mockReturnValue({
      isLoading: false,
      error: null,
      data: undefined,
    })
    render(<PublicDashboard />)
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
  })
})
