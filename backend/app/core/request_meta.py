from __future__ import annotations

from ipaddress import ip_address
from typing import Optional

from fastapi import Request

from app.config import get_settings

settings = get_settings()


def _normalize_ip(value: str) -> Optional[str]:
    candidate = value.strip()
    if not candidate:
        return None
    try:
        return str(ip_address(candidate))
    except ValueError:
        return None


def get_request_ip(request: Request) -> Optional[str]:
    if settings.trust_x_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        first_hop = forwarded.split(",")[0] if forwarded else ""
        forwarded_ip = _normalize_ip(first_hop)
        if forwarded_ip:
            return forwarded_ip

    if request.client and request.client.host:
        client_ip = _normalize_ip(request.client.host)
        if client_ip:
            return client_ip
        return request.client.host

    return None


def get_request_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("user-agent")
