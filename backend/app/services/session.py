from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_csrf_token_value,
    create_refresh_token_value,
    hash_token
)
from app.db.models import RefreshToken, User
from app.services.security_store import get_security_store

settings = get_settings()


@dataclass
class SessionBundle:
    access_token: str
    refresh_token: str
    csrf_token: str
    session_id: str
    session_expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_access_token(username: str, session_id: str) -> str:
    return create_access_token(
        {"sub": username, "sid": session_id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_session_tokens(
    db: Session,
    *,
    user: User,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> SessionBundle:
    refresh_token = create_refresh_token_value()
    csrf_token = create_csrf_token_value()
    session_id = uuid.uuid4().hex
    expires_at = _utcnow() + timedelta(days=settings.refresh_token_expire_days)

    row = RefreshToken(
        user_id=user.id,
        session_id=session_id,
        token_hash=hash_token(refresh_token),
        csrf_token=csrf_token,
        expires_at=expires_at,
        created_ip=ip,
        created_user_agent=user_agent
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return SessionBundle(
        access_token=_build_access_token(user.username, session_id),
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        session_id=session_id,
        session_expires_at=expires_at
    )


def _get_active_refresh_row(db: Session, refresh_token: str) -> Optional[RefreshToken]:
    now = _utcnow()
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(refresh_token),
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > now
    ).first()


def rotate_session_tokens(
    db: Session,
    *,
    refresh_token: str,
    csrf_token: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[SessionBundle]:
    now = _utcnow()
    current = _get_active_refresh_row(db, refresh_token)
    if current is None:
        return None
    if current.csrf_token != csrf_token:
        return None
    if is_access_session_revoked(current.session_id):
        return None

    current.revoked_at = now
    current.last_used_at = now

    new_refresh = create_refresh_token_value()
    new_csrf = create_csrf_token_value()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    rotated = RefreshToken(
        user_id=current.user_id,
        session_id=current.session_id,
        token_hash=hash_token(new_refresh),
        csrf_token=new_csrf,
        expires_at=expires_at,
        created_ip=ip,
        created_user_agent=user_agent
    )
    db.add(rotated)
    db.commit()
    db.refresh(rotated)

    user = current.user
    if user is None:
        return None

    return SessionBundle(
        access_token=_build_access_token(user.username, current.session_id),
        refresh_token=new_refresh,
        csrf_token=new_csrf,
        session_id=current.session_id,
        session_expires_at=expires_at
    )


def revoke_refresh_session(db: Session, refresh_token: str) -> Optional[RefreshToken]:
    row = _get_active_refresh_row(db, refresh_token)
    if row is None:
        return None

    row.revoked_at = _utcnow()
    row.last_used_at = _utcnow()
    db.commit()
    db.refresh(row)

    revoke_access_session(row.session_id)
    return row


def revoke_access_session(session_id: str) -> None:
    ttl_seconds = settings.access_token_expire_minutes * 60
    get_security_store().set_with_ttl(f"revoked_session:{session_id}", "1", ttl_seconds)


def is_access_session_revoked(session_id: str) -> bool:
    return get_security_store().get_value(f"revoked_session:{session_id}") == "1"
