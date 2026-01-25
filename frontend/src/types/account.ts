export type AccountStatus = 'pending' | 'approved' | 'in_copy' | 'expired' | 'suspended'

export interface Account {
  id: number
  account_number: string
  account_password: string
  server: string
  buyer_name: string
  buyer_email: string | null
  buyer_phone: string | null
  buyer_notes: string | null
  purchase_date: string
  expiry_date: string | null
  purchase_price: number | null
  status: AccountStatus
  copy_count: number
  max_copies: number
  created_at: string
  updated_at: string | null
  created_by: number | null
}

export interface AccountCreate {
  account_number: string
  account_password: string
  server: string
  buyer_name: string
  buyer_email?: string
  buyer_phone?: string
  buyer_notes?: string
  purchase_date: string
  expiry_date?: string
  purchase_price?: number
  status?: AccountStatus
  max_copies?: number
}

export interface AccountUpdate extends Partial<AccountCreate> {
  copy_count?: number
}

export interface Stats {
  total_accounts: number
  pending: number
  approved: number
  in_copy: number
  expired: number
  suspended: number
}

export interface AdminStats extends Stats {
  total_revenue: number
  accounts_this_month: number
}
