from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import require_admin_v2, require_csrf
from app.core.request_meta import get_request_ip, get_request_user_agent
from app.core.security import verify_password
from app.crud.account import (
    build_account_response_v2,
    create_account,
    delete_account,
    get_account,
    get_account_by_number,
    get_accounts,
    get_admin_stats,
    reveal_account_password,
    rotate_account_password,
    update_account,
    update_account_status,
)
from app.db.database import get_db
from app.db.models import User
from app.schemas.account import (
    AccountAdminV2Response,
    AccountCreate,
    AccountUpdateV2,
    AdminStatsResponse,
    PasswordRevealRequest,
    PasswordRevealResponse,
    PasswordRotateRequest,
    StatusUpdate,
)
from app.services.audit import log_security_event
from app.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/api/v2/admin", tags=["admin-v2"])
settings = get_settings()


@router.get("/accounts", response_model=list[AccountAdminV2Response])
async def list_accounts_v2(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    accounts = get_accounts(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        search=search
    )
    return [build_account_response_v2(acc) for acc in accounts]


@router.get("/accounts/{account_id}", response_model=AccountAdminV2Response)
async def get_account_detail_v2(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return build_account_response_v2(account)


@router.post(
    "/accounts",
    response_model=AccountAdminV2Response,
    status_code=201,
    dependencies=[Depends(require_csrf)]
)
async def create_new_account_v2(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    existing = get_account_by_number(db, account_data.account_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Numero da conta ja existe"
        )
    account = create_account(db, account_data, current_user.id)
    return build_account_response_v2(account)


@router.put(
    "/accounts/{account_id}",
    response_model=AccountAdminV2Response,
    dependencies=[Depends(require_csrf)]
)
async def update_existing_account_v2(
    account_id: int,
    account_data: AccountUpdateV2,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
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
    return build_account_response_v2(account)


@router.patch(
    "/accounts/{account_id}/status",
    response_model=AccountAdminV2Response,
    dependencies=[Depends(require_csrf)]
)
async def update_status_v2(
    account_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
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
    return build_account_response_v2(account)


@router.delete(
    "/accounts/{account_id}",
    status_code=204,
    dependencies=[Depends(require_csrf)]
)
async def delete_existing_account_v2(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    success = delete_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )
    return None


@router.get("/stats", response_model=AdminStatsResponse)
async def get_statistics_v2(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    return get_admin_stats(db)


@router.post(
    "/accounts/{account_id}/password/reveal",
    response_model=PasswordRevealResponse,
    dependencies=[Depends(require_csrf)]
)
async def reveal_account_password_v2(
    account_id: int,
    reveal_data: PasswordRevealRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    ip = get_request_ip(request)
    user_agent = get_request_user_agent(request)
    try:
        enforce_rate_limit(
            namespace="reveal_user",
            identifier=str(current_user.id),
            limit=3,
            window_seconds=600
        )
    except HTTPException:
        log_security_event(
            db,
            action="account_password_reveal_rate_limit",
            success=False,
            user_id=current_user.id,
            target_type="copy_trade_account",
            target_id=str(account_id),
            reason="rate_limit_exceeded",
            ip=ip,
            user_agent=user_agent
        )
        raise

    account = get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )

    if not verify_password(reveal_data.admin_password, current_user.hashed_password):
        log_security_event(
            db,
            action="account_password_reveal",
            success=False,
            user_id=current_user.id,
            target_type="copy_trade_account",
            target_id=str(account_id),
            reason="invalid_admin_password",
            ip=ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha do admin invalida"
        )

    password = reveal_account_password(account)
    log_security_event(
        db,
        action="account_password_reveal",
        success=True,
        user_id=current_user.id,
        target_type="copy_trade_account",
        target_id=str(account_id),
        ip=ip,
        user_agent=user_agent
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return PasswordRevealResponse(
        account_password=password,
        revealed_at=datetime.now(timezone.utc),
        expires_in_seconds=settings.password_reveal_ttl_seconds
    )


@router.post(
    "/accounts/{account_id}/password/rotate",
    response_model=AccountAdminV2Response,
    dependencies=[Depends(require_csrf)]
)
async def rotate_account_password_v2(
    account_id: int,
    rotate_data: PasswordRotateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_v2)
):
    account = rotate_account_password(db, account_id, rotate_data.new_password)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada"
        )

    log_security_event(
        db,
        action="account_password_rotate",
        success=True,
        user_id=current_user.id,
        target_type="copy_trade_account",
        target_id=str(account_id),
        ip=get_request_ip(request),
        user_agent=get_request_user_agent(request)
    )
    return build_account_response_v2(account)
