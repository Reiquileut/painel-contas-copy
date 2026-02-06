from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import SecurityAuditLog


def log_security_event(
    db: Session,
    *,
    action: str,
    success: bool,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    reason: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    event = SecurityAuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        success=success,
        reason=reason,
        ip=ip,
        user_agent=user_agent
    )
    try:
        db.add(event)
        db.commit()
    except Exception:
        db.rollback()
