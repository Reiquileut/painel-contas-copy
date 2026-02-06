from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import app.main as main_module
from app.api import accounts_v2 as accounts_v2_module
from app.api import auth_v2 as auth_v2_module
from app.config import Settings, get_settings
from app.core.dependencies import get_current_user_v2, require_csrf
from app.core.security import create_access_token
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.services import rate_limit, security_store
from app.services.session import (
    create_session_tokens,
    revoke_access_session,
    revoke_refresh_session,
    rotate_session_tokens
)


def _make_request(method: str, cookies: dict[str, str] | None = None, headers: dict[str, str] | None = None):
    cookie_header = ""
    if cookies:
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
    raw_headers = []
    if cookie_header:
        raw_headers.append((b"cookie", cookie_header.encode()))
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode(), value.encode()))
    scope = {"type": "http", "method": method, "headers": raw_headers}
    return Request(scope)


def _run(coro):
    return asyncio.run(coro)


def test_settings_security_validations(monkeypatch):
    for key in (
        "JWT_SECRET_KEY",
        "ENCRYPTION_KEY",
        "ADMIN_PASSWORD",
        "REDIS_URL",
        "CORS_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)

    dev_settings = Settings(app_env="test", jwt_secret_key="", encryption_key="")
    assert len(dev_settings.jwt_secret_key) >= 32
    assert len(dev_settings.encryption_key) >= 40
    assert dev_settings.cookie_secure is False
    assert dev_settings.docs_enabled is True
    assert dev_settings.v1_sunset_at > dev_settings.v1_deprecation_start_at
    assert "GMT" in dev_settings.v1_sunset_http
    generated_admin = Settings(
        app_env="test",
        jwt_secret_key="x" * 32,
        encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        admin_password=""
    )
    assert generated_admin.admin_password
    naive_time = Settings(
        app_env="test",
        jwt_secret_key="x" * 32,
        encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        v1_deprecation_start="2026-02-06T00:00:00"
    )
    assert naive_time.v1_deprecation_start_at.tzinfo == timezone.utc

    with pytest.raises(ValueError, match="greater than zero"):
        Settings(
            app_env="test",
            jwt_secret_key="x" * 32,
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            access_token_expire_minutes=0
        )

    with pytest.raises(ValueError, match="JWT_SECRET_KEY is required in production"):
        Settings(
            app_env="production",
            jwt_secret_key="",
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="123456789012",
            redis_url="redis://localhost:6379/0"
        )

    with pytest.raises(ValueError, match="at least 32 chars"):
        Settings(
            app_env="production",
            jwt_secret_key="short",
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="123456789012",
            redis_url="redis://localhost:6379/0"
        )

    with pytest.raises(ValueError, match="ENCRYPTION_KEY is required in production"):
        Settings(
            app_env="production",
            jwt_secret_key="x" * 32,
            encryption_key="",
            admin_password="123456789012",
            redis_url="redis://localhost:6379/0"
        )

    with pytest.raises(ValueError, match="ADMIN_PASSWORD is required in production"):
        Settings(
            app_env="production",
            jwt_secret_key="x" * 32,
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="",
            redis_url="redis://localhost:6379/0"
        )

    with pytest.raises(ValueError, match="at least 12 chars"):
        Settings(
            app_env="production",
            jwt_secret_key="x" * 32,
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="short",
            redis_url="redis://localhost:6379/0"
        )

    with pytest.raises(ValueError, match="REDIS_URL is required in production"):
        Settings(
            app_env="production",
            jwt_secret_key="x" * 32,
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="123456789012",
            redis_url=""
        )

    with pytest.raises(ValueError, match="cannot contain '\\*'"):
        Settings(
            app_env="production",
            jwt_secret_key="x" * 32,
            encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            admin_password="123456789012",
            redis_url="redis://localhost:6379/0",
            cors_origins="*"
        )


def test_csrf_dependency_validation():
    settings = get_settings()
    ok_request = _make_request(
        "POST",
        cookies={settings.session_cookie_name_csrf: "abc"},
        headers={settings.csrf_header_name: "abc"}
    )
    require_csrf(ok_request)

    invalid_request = _make_request(
        "POST",
        cookies={settings.session_cookie_name_csrf: "abc"},
        headers={settings.csrf_header_name: "wrong"}
    )
    with pytest.raises(HTTPException) as exc:
        require_csrf(invalid_request)
    assert exc.value.status_code == 403

    safe_request = _make_request("GET")
    require_csrf(safe_request)


def test_get_current_user_v2_and_session_revocation(db_session):
    user = user_crud.create_user(
        db_session,
        UserCreate(
            username="cookie-user",
            email="cookie-user@example.com",
            password="strong-password",
            is_admin=True
        )
    )
    token = create_access_token({"sub": user.username, "sid": "session-1"})
    request = _make_request(
        "GET",
        cookies={get_settings().session_cookie_name_access: token}
    )
    current = _run(get_current_user_v2(request=request, db=db_session))
    assert current.username == "cookie-user"

    revoke_access_session("session-1")
    with pytest.raises(HTTPException) as exc:
        _run(get_current_user_v2(request=request, db=db_session))
    assert exc.value.status_code == 401

    token_without_sid = create_access_token({"sub": user.username})
    no_sid_request = _make_request(
        "GET",
        cookies={get_settings().session_cookie_name_access: token_without_sid}
    )
    with pytest.raises(HTTPException) as no_sid_exc:
        _run(get_current_user_v2(request=no_sid_request, db=db_session))
    assert no_sid_exc.value.status_code == 401


def test_rate_limit_and_security_store_inmemory():
    security_store._store_cache = security_store.InMemorySecurityStore()
    store = security_store.get_security_store()
    store.set_with_ttl("k1", "v1", 60)
    assert store.get_value("k1") == "v1"

    allowed, _, _ = rate_limit.check_rate_limit("demo", "id-1", 2, 60)
    assert allowed is True
    allowed, _, _ = rate_limit.check_rate_limit("demo", "id-1", 2, 60)
    assert allowed is True
    with pytest.raises(HTTPException) as exc:
        rate_limit.enforce_rate_limit("demo", "id-1", 2, 60)
    assert exc.value.status_code == 429


def test_security_store_redis_and_production_branches(monkeypatch):
    import app.services.security_store as store_module

    class FakePipeline:
        def __init__(self, client):
            self.client = client

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def incr(self, key):
            self.client.counter += 1

        def ttl(self, key):
            return None

        def execute(self):
            return self.client.counter, -1

    class FakeRedisClient:
        def __init__(self):
            self.counter = 0
            self.values = {}

        def ping(self):
            return True

        def pipeline(self):
            return FakePipeline(self)

        def expire(self, key, ttl):
            self.values[f"ttl:{key}"] = str(ttl)

        def setex(self, key, ttl, value):
            self.values[key] = value

        def get(self, key):
            return self.values.get(key)

    fake_client = FakeRedisClient()

    class FakeRedisFactory:
        @staticmethod
        def from_url(*args, **kwargs):
            return fake_client

    monkeypatch.setattr(store_module, "Redis", FakeRedisFactory)
    monkeypatch.setattr(store_module, "RedisError", RuntimeError)
    monkeypatch.setattr(store_module.settings, "redis_url", "redis://fake")
    monkeypatch.setattr(store_module.settings, "app_env", "test")
    store_module._redis_cache = None
    store_module._store_cache = None

    redis_client = store_module.get_redis_client()
    assert redis_client is fake_client
    assert store_module.is_redis_available() is True

    redis_store = store_module.get_security_store()
    count, ttl = redis_store.incr_with_window("k", 60)
    assert count == 1
    assert ttl >= 1
    redis_store.set_with_ttl("kv", "v", 10)
    assert redis_store.get_value("kv") == "v"
    assert redis_store.get_value("missing") is None

    class ExplodingRedisClient(FakeRedisClient):
        def pipeline(self):
            raise RuntimeError("boom")

        def setex(self, key, ttl, value):
            raise RuntimeError("boom")

        def get(self, key):
            raise RuntimeError("boom")

    exploding_store = store_module.RedisSecurityStore(ExplodingRedisClient())
    assert exploding_store.incr_with_window("k", 60) == (1, 60)
    exploding_store.set_with_ttl("kv", "v", 10)
    assert exploding_store.get_value("kv") is None

    class BrokenRedisFactory:
        @staticmethod
        def from_url(*args, **kwargs):
            raise RuntimeError("offline")

    store_module._redis_cache = None
    store_module._store_cache = None
    monkeypatch.setattr(store_module, "Redis", BrokenRedisFactory)
    assert store_module.get_redis_client() is None

    monkeypatch.setattr(store_module.settings, "app_env", "production")
    monkeypatch.setattr(store_module.settings, "redis_url", "")
    store_module._store_cache = None
    with pytest.raises(RuntimeError, match="Redis is required"):
        store_module.get_security_store()

    monkeypatch.setattr(store_module.settings, "app_env", "test")
    monkeypatch.setattr(store_module.settings, "redis_url", "")
    store_module._store_cache = None
    assert isinstance(store_module.get_security_store(), store_module.InMemorySecurityStore)


def test_request_ip_helpers_cover_forwarded_and_client_scope():
    forwarded = _make_request("GET", headers={"X-Forwarded-For": "198.51.100.1, 203.0.113.1"})
    assert accounts_v2_module._request_ip(forwarded) == "198.51.100.1"
    assert auth_v2_module._request_ip(forwarded) == "198.51.100.1"

    client_scope = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )
    assert accounts_v2_module._request_ip(client_scope) == "127.0.0.1"
    assert auth_v2_module._request_ip(client_scope) == "127.0.0.1"


def test_session_service_create_rotate_and_revoke(db_session):
    security_store._store_cache = security_store.InMemorySecurityStore()
    user = user_crud.create_user(
        db_session,
        UserCreate(
            username="session-user",
            email="session-user@example.com",
            password="strong-password",
            is_admin=True
        )
    )

    created = create_session_tokens(db_session, user=user, ip="127.0.0.1", user_agent="pytest")
    assert created.access_token
    assert created.refresh_token
    assert created.csrf_token

    assert rotate_session_tokens(
        db_session,
        refresh_token=created.refresh_token,
        csrf_token="bad-csrf"
    ) is None

    rotated = rotate_session_tokens(
        db_session,
        refresh_token=created.refresh_token,
        csrf_token=created.csrf_token,
        ip="127.0.0.1",
        user_agent="pytest"
    )
    assert rotated is not None
    assert rotated.refresh_token != created.refresh_token

    revoked = revoke_refresh_session(db_session, rotated.refresh_token)
    assert revoked is not None
    assert revoke_refresh_session(db_session, "non-existent") is None

    # Unknown token branch in rotate
    assert rotate_session_tokens(
        db_session,
        refresh_token="unknown-token",
        csrf_token="anything"
    ) is None

    revoked_session = create_session_tokens(db_session, user=user)
    revoke_access_session(revoked_session.session_id)
    assert rotate_session_tokens(
        db_session,
        refresh_token=revoked_session.refresh_token,
        csrf_token=revoked_session.csrf_token
    ) is None


def test_session_service_rotate_user_missing_branch(monkeypatch, db_session):
    import app.services.session as session_module

    class FakeToken:
        csrf_token = "csrf"
        session_id = "sid-123"
        user_id = 1
        user = None
        revoked_at = None
        last_used_at = None

    monkeypatch.setattr(session_module, "_get_active_refresh_row", lambda db, refresh: FakeToken())
    monkeypatch.setattr(session_module, "is_access_session_revoked", lambda _: False)

    assert session_module.rotate_session_tokens(
        db_session,
        refresh_token="any",
        csrf_token="csrf"
    ) is None


def test_main_deprecation_headers_and_sunset_guard(client, db_session, monkeypatch):
    user_crud.create_user(
        db_session,
        UserCreate(
            username="legacy-user",
            email="legacy-user@example.com",
            password="strong-password",
            is_admin=True
        )
    )

    # v1 still available and flagged as deprecated
    legacy_login = client.post(
        "/api/auth/login",
        json={"username": "legacy-user", "password": "strong-password"}
    )
    assert legacy_login.status_code == 200
    assert legacy_login.headers.get("Deprecation") == "true"
    assert legacy_login.headers.get("Sunset")

    # Force sunset
    monkeypatch.setattr(main_module.settings, "v1_deprecation_start", "2000-01-01T00:00:00+00:00")
    monkeypatch.setattr(main_module.settings, "v1_deprecation_window_days", 1)
    gone = client.post("/api/auth/login", json={"username": "x", "password": "y"})
    assert gone.status_code == 410
    assert gone.json()["detail"] == "API v1 descontinuada. Use /api/v2."


def test_startup_security_checks_production_requires_redis(monkeypatch):
    monkeypatch.setattr(main_module.settings, "app_env", "production")
    monkeypatch.setattr(main_module, "is_redis_available", lambda: False)
    with pytest.raises(RuntimeError, match="Redis must be reachable"):
        _run(main_module.startup_security_checks())

    monkeypatch.setattr(main_module.settings, "app_env", "test")
    _run(main_module.startup_security_checks())


def test_audit_service_rollback_branch():
    from app.services.audit import log_security_event

    class BrokenSession:
        def add(self, event):
            raise RuntimeError("boom")

        def commit(self):
            raise RuntimeError("boom")

        def rollback(self):
            self.rolled_back = True

    broken = BrokenSession()
    log_security_event(broken, action="test", success=False)
    assert getattr(broken, "rolled_back", False) is True
