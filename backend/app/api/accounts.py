from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.db.models import User
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountAdminResponse,
    StatusUpdate,
    AdminStatsResponse
)
from app.crud.account import (
    get_accounts,
    get_account,
    get_account_by_number,
    create_account,
    update_account,
    update_account_status,
    delete_account,
    get_admin_stats,
    decrypt_account_for_response
)
from app.core.dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/accounts", response_model=list[AccountAdminResponse])
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    accounts = get_accounts(db, skip=skip, limit=limit, status=status, search=search)
    return [decrypt_account_for_response(acc) for acc in accounts]


@router.get("/accounts/{account_id}", response_model=AccountAdminResponse)
async def get_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return decrypt_account_for_response(account)


@router.post("/accounts", response_model=AccountAdminResponse, status_code=201)
async def create_new_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Check if account number already exists
    existing = get_account_by_number(db, account_data.account_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Numero da conta ja existe"
        )

    account = create_account(db, account_data, current_user.id)
    return decrypt_account_for_response(account)


@router.put("/accounts/{account_id}", response_model=AccountAdminResponse)
async def update_existing_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Check if changing account number to one that already exists
    if account_data.account_number:
        existing = get_account_by_number(db, account_data.account_number)
        if existing and existing.id != account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Numero da conta ja existe"
            )

    account = update_account(db, account_id, account_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return decrypt_account_for_response(account)


@router.patch("/accounts/{account_id}/status", response_model=AccountAdminResponse)
async def update_status(
    account_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    valid_statuses = ["pending", "approved", "in_copy", "expired", "suspended"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status invalido. Valores validos: {valid_statuses}"
        )

    account = update_account_status(db, account_id, status_data.status)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return decrypt_account_for_response(account)


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_existing_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    success = delete_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return None


@router.get("/stats", response_model=AdminStatsResponse)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_admin_stats(db)
