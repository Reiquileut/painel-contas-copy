import type { Account, AdminStats, Stats } from '../types/account'
import type { User } from '../types/auth'

export const mockUser: User = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  is_active: true,
  is_admin: true,
  created_at: '2026-01-01T00:00:00Z',
}

export const mockStats: Stats = {
  total_accounts: 10,
  pending: 2,
  approved: 3,
  in_copy: 4,
  expired: 1,
  suspended: 0,
}

export const mockAdminStats: AdminStats = {
  ...mockStats,
  total_revenue: 999.99,
  accounts_this_month: 5,
}

export const mockAccount: Account = {
  id: 1,
  account_number: 'ACC-1',
  server: 'MT5',
  buyer_name: 'Buyer',
  buyer_email: 'buyer@example.com',
  buyer_phone: '1199999999',
  buyer_notes: 'notes',
  purchase_date: '2026-01-01',
  expiry_date: '2026-02-01',
  purchase_price: 100,
  status: 'pending',
  copy_count: 0,
  max_copies: 2,
  margin_size: 2000,
  phase1_target: 500,
  phase1_status: 'in_progress',
  phase2_target: 300,
  phase2_status: 'not_started',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: null,
  created_by: 1,
}
