from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional, Any
from decimal import Decimal
from app.db.models import CopyTradeAccount
from app.schemas.account import AccountCreate, AccountUpdate, AccountUpdateV2
from app.core.security import encrypt_account_password, decrypt_account_password


def get_accounts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> list[CopyTradeAccount]:
    query = db.query(CopyTradeAccount)
    if status:
        query = query.filter(CopyTradeAccount.status == status)
    if search:
        query = query.filter(CopyTradeAccount.buyer_name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_account(db: Session, account_id: int) -> CopyTradeAccount | None:
    return db.query(CopyTradeAccount).filter(
        CopyTradeAccount.id == account_id
    ).first()


def get_account_by_number(
    db: Session,
    account_number: str
) -> CopyTradeAccount | None:
    return db.query(CopyTradeAccount).filter(
        CopyTradeAccount.account_number == account_number
    ).first()


def create_account(
    db: Session,
    account: AccountCreate,
    user_id: int
) -> CopyTradeAccount:
    # Encrypt the account password
    encrypted_password = encrypt_account_password(account.account_password)

    db_account = CopyTradeAccount(
        account_number=account.account_number,
        account_password=encrypted_password,
        server=account.server,
        buyer_name=account.buyer_name,
        buyer_email=account.buyer_email,
        buyer_phone=account.buyer_phone,
        buyer_notes=account.buyer_notes,
        purchase_date=account.purchase_date,
        expiry_date=account.expiry_date,
        purchase_price=account.purchase_price,
        status=account.status,
        max_copies=account.max_copies,
        margin_size=account.margin_size,
        phase1_target=account.phase1_target,
        phase1_status=account.phase1_status,
        phase2_target=account.phase2_target,
        phase2_status=account.phase2_status,
        created_by=user_id
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_account(
    db: Session,
    account_id: int,
    account_update: AccountUpdate | AccountUpdateV2
) -> CopyTradeAccount | None:
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    update_data = account_update.model_dump(exclude_unset=True)

    # Encrypt password if being updated
    if "account_password" in update_data and update_data["account_password"]:
        update_data["account_password"] = encrypt_account_password(
            update_data["account_password"]
        )

    for field, value in update_data.items():
        setattr(db_account, field, value)

    db.commit()
    db.refresh(db_account)
    return db_account


def update_account_status(
    db: Session,
    account_id: int,
    status: str
) -> CopyTradeAccount | None:
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    db_account.status = status
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_account(db: Session, account_id: int) -> bool:
    db_account = get_account(db, account_id)
    if not db_account:
        return False

    db.delete(db_account)
    db.commit()
    return True


def get_stats(db: Session) -> dict:
    total = db.query(func.count(CopyTradeAccount.id)).scalar() or 0
    pending = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.status == "pending"
    ).scalar() or 0
    approved = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.status == "approved"
    ).scalar() or 0
    in_copy = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.status == "in_copy"
    ).scalar() or 0
    expired = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.status == "expired"
    ).scalar() or 0
    suspended = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.status == "suspended"
    ).scalar() or 0

    return {
        "total_accounts": total,
        "pending": pending,
        "approved": approved,
        "in_copy": in_copy,
        "expired": expired,
        "suspended": suspended
    }


def get_admin_stats(db: Session) -> dict:
    stats = get_stats(db)

    # Total revenue
    total_revenue = db.query(
        func.coalesce(func.sum(CopyTradeAccount.purchase_price), 0)
    ).scalar() or Decimal("0")

    # Accounts created this month
    today = date.today()
    first_of_month = today.replace(day=1)
    accounts_this_month = db.query(func.count(CopyTradeAccount.id)).filter(
        CopyTradeAccount.purchase_date >= first_of_month
    ).scalar() or 0

    return {
        **stats,
        "total_revenue": total_revenue,
        "accounts_this_month": accounts_this_month
    }


def decrypt_account_for_response(account: CopyTradeAccount) -> dict:
    """Legacy helper retained for compatibility tests."""
    return build_account_response(account, include_password=True)


def reveal_account_password(account: CopyTradeAccount) -> str:
    return decrypt_account_password(account.account_password)


def rotate_account_password(
    db: Session,
    account_id: int,
    new_password: str
) -> CopyTradeAccount | None:
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    db_account.account_password = encrypt_account_password(new_password)
    db.commit()
    db.refresh(db_account)
    return db_account


def build_account_response(
    account: CopyTradeAccount,
    *,
    include_password: bool = False,
    mask_password: bool = False
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": account.id,
        "account_number": account.account_number,
        "server": account.server,
        "buyer_name": account.buyer_name,
        "buyer_email": account.buyer_email,
        "buyer_phone": account.buyer_phone,
        "buyer_notes": account.buyer_notes,
        "purchase_date": account.purchase_date,
        "expiry_date": account.expiry_date,
        "purchase_price": account.purchase_price,
        "status": account.status,
        "copy_count": account.copy_count,
        "max_copies": account.max_copies,
        "margin_size": account.margin_size,
        "phase1_target": account.phase1_target,
        "phase1_status": account.phase1_status,
        "phase2_target": account.phase2_target,
        "phase2_status": account.phase2_status,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "created_by": account.created_by
    }
    if include_password:
        data["account_password"] = decrypt_account_password(account.account_password)
    elif mask_password:
        data["account_password"] = "********"  # nosec
    return data


def build_account_response_v1(account: CopyTradeAccount) -> dict[str, Any]:
    return build_account_response(account, mask_password=True)


def build_account_response_v2(account: CopyTradeAccount) -> dict[str, Any]:
    return build_account_response(account)
