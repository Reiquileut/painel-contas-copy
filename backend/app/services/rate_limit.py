from __future__ import annotations

from fastapi import HTTPException, status

from app.services.security_store import get_security_store


def check_rate_limit(
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int
) -> tuple[bool, int, int]:
    key = f"rl:{namespace}:{identifier}"
    count, retry_after = get_security_store().incr_with_window(key, window_seconds)
    return count <= limit, retry_after, count


def enforce_rate_limit(
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int
) -> None:
    allowed, retry_after, current_count = check_rate_limit(
        namespace=namespace,
        identifier=identifier,
        limit=limit,
        window_seconds=window_seconds
    )
    if allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "code": "rate_limit_exceeded",
            "namespace": namespace,
            "limit": limit,
            "window_seconds": window_seconds,
            "current_count": current_count,
        },
        headers={"Retry-After": str(retry_after)}
    )
