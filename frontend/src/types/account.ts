export type AccountStatus = 'pending' | 'approved' | 'in_copy' | 'expired' | 'suspended'
export type PhaseStatus = 'not_started' | 'in_progress' | 'passed' | 'failed'

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
  margin_size: number | null
  phase1_target: number | null
  phase1_status: PhaseStatus | null
  phase2_target: number | null
  phase2_status: PhaseStatus | null
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
  margin_size?: number
  phase1_target?: number
  phase1_status?: PhaseStatus
  phase2_target?: number
  phase2_status?: PhaseStatus
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
