from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user_v2, require_csrf
from app.core.request_meta import get_request_ip, get_request_user_agent
from app.crud.user import authenticate_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import LoginRequest, MessageResponse, SessionLoginResponse, UserResponse
from app.services.audit import log_security_event
from app.services.rate_limit import enforce_rate_limit
from app.services.session import create_session_tokens, revoke_refresh_session, rotate_session_tokens

router = APIRouter(prefix="/api/v2/auth", tags=["auth-v2"])
settings = get_settings()


def _set_session_cookies(response: Response, *, access_token: str, refresh_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name_access,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/"
    )
    response.set_cookie(
        key=settings.session_cookie_name_refresh,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/api/v2/auth"
    )
    response.set_cookie(
        key=settings.session_cookie_name_csrf,
        value=csrf_token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/"
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(key=settings.session_cookie_name_access, path="/")
    response.delete_cookie(key=settings.session_cookie_name_refresh, path="/api/v2/auth")
    response.delete_cookie(key=settings.session_cookie_name_csrf, path="/")


def _set_no_store_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post("/login", response_model=SessionLoginResponse)
async def login_v2(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_request_ip(request) or "unknown"
    user_agent = get_request_user_agent(request)

    try:
        enforce_rate_limit("login_ip", ip, limit=5, window_seconds=60)
        enforce_rate_limit(
            "login_username",
            login_data.username.lower(),
            limit=20,
            window_seconds=3600
        )
    except HTTPException:
        log_security_event(
            db,
            action="auth_login_rate_limit",
            success=False,
            target_type="user",
            target_id=login_data.username,
            reason="rate_limit_exceeded",
            ip=ip,
            user_agent=user_agent
        )
        raise

    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        log_security_event(
            db,
            action="auth_login",
            success=False,
            target_type="user",
            target_id=login_data.username,
            reason="invalid_credentials",
            ip=ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario ou senha incorretos"
        )

    session_bundle = create_session_tokens(
        db,
        user=user,
        ip=ip,
        user_agent=user_agent
    )
    _set_session_cookies(
        response,
        access_token=session_bundle.access_token,
        refresh_token=session_bundle.refresh_token,
        csrf_token=session_bundle.csrf_token
    )
    _set_no_store_headers(response)
    log_security_event(
        db,
        action="auth_login",
        success=True,
        user_id=user.id,
        ip=ip,
        user_agent=user_agent
    )
    return SessionLoginResponse(
        user=UserResponse.model_validate(user),
        session_expires_at=session_bundle.session_expires_at
    )


@router.post("/refresh", status_code=204, dependencies=[Depends(require_csrf)])
async def refresh_v2(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    refresh_token = request.cookies.get(settings.session_cookie_name_refresh)
    csrf_token = request.cookies.get(settings.session_cookie_name_csrf)
    ip = get_request_ip(request)
    user_agent = get_request_user_agent(request)

    if not refresh_token or not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao invalida"
        )

    try:
        enforce_rate_limit(
            "refresh_session",
            refresh_token[:16],
            limit=10,
            window_seconds=60
        )
    except HTTPException:
        log_security_event(
            db,
            action="auth_refresh_rate_limit",
            success=False,
            reason="rate_limit_exceeded",
            ip=ip,
            user_agent=user_agent
        )
        raise

    rotated = rotate_session_tokens(
        db,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        ip=ip,
        user_agent=user_agent
    )
    if rotated is None:
        log_security_event(
            db,
            action="auth_refresh",
            success=False,
            reason="invalid_refresh",
            ip=ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao invalida"
        )

    _set_session_cookies(
        response,
        access_token=rotated.access_token,
        refresh_token=rotated.refresh_token,
        csrf_token=rotated.csrf_token
    )
    _set_no_store_headers(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
async def me_v2(
    response: Response,
    current_user: User = Depends(get_current_user_v2)
):
    _set_no_store_headers(response)
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    dependencies=[Depends(require_csrf)]
)
async def logout_v2(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_v2)
):
    refresh_token = request.cookies.get(settings.session_cookie_name_refresh)
    ip = get_request_ip(request)
    user_agent = get_request_user_agent(request)
    if refresh_token:
        revoke_refresh_session(db, refresh_token)

    _clear_session_cookies(response)
    _set_no_store_headers(response)
    log_security_event(
        db,
        action="auth_logout",
        success=True,
        user_id=current_user.id,
        ip=ip,
        user_agent=user_agent
    )
    return MessageResponse(message="Logout realizado com sucesso")
