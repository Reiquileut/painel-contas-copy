from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class AccountBase(BaseModel):
    account_number: str
    server: str
    buyer_name: str
    buyer_email: Optional[EmailStr] = None
    buyer_phone: Optional[str] = None
    buyer_notes: Optional[str] = None
    purchase_date: date
    expiry_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    status: str = "pending"
    max_copies: int = 1


class AccountCreate(AccountBase):
    account_password: str


class AccountUpdate(BaseModel):
    account_number: Optional[str] = None
    account_password: Optional[str] = None
    server: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_email: Optional[EmailStr] = None
    buyer_phone: Optional[str] = None
    buyer_notes: Optional[str] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    status: Optional[str] = None
    copy_count: Optional[int] = None
    max_copies: Optional[int] = None


class StatusUpdate(BaseModel):
    status: str


# Response for admin (all data)
class AccountAdminResponse(AccountBase):
    id: int
    account_password: str  # Decrypted for admin view
    copy_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# Response for public (filtered data)
class AccountPublicResponse(BaseModel):
    id: int
    status: str
    server: str
    copy_count: int
    max_copies: int
    is_available: bool

    class Config:
        from_attributes = True


# Stats response
class StatsResponse(BaseModel):
    total_accounts: int
    pending: int
    approved: int
    in_copy: int
    expired: int
    suspended: int


class AdminStatsResponse(StatsResponse):
    total_revenue: Decimal
    accounts_this_month: int
