from app.config import get_settings
from app.crud import user as user_crud
from app.db.models import SecurityAuditLog
from app.schemas.user import UserCreate
from app.services import security_store

settings = get_settings()


def create_admin(db_session, username: str = "admin-v2"):
    return user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=True
        )
    )


def csrf_headers(client):
    csrf_token = client.cookies.get(settings.session_cookie_name_csrf)
    return {settings.csrf_header_name: csrf_token} if csrf_token else {}


def test_auth_v2_login_me_refresh_logout_flow(client, db_session):
    create_admin(db_session)

    login = client.post(
        "/api/v2/auth/login",
        json={"username": "admin-v2", "password": "strong-password"}
    )
    assert login.status_code == 200
    body = login.json()
    assert body["user"]["username"] == "admin-v2"
    assert "session_expires_at" in body

    set_cookie = login.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "SameSite" in set_cookie
    assert client.cookies.get(settings.session_cookie_name_access)
    assert client.cookies.get(settings.session_cookie_name_refresh)
    assert client.cookies.get(settings.session_cookie_name_csrf)

    me = client.get("/api/v2/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "admin-v2"

    missing_csrf = client.post("/api/v2/auth/refresh")
    assert missing_csrf.status_code == 403

    refreshed = client.post("/api/v2/auth/refresh", headers=csrf_headers(client))
    assert refreshed.status_code == 204
    assert client.cookies.get(settings.session_cookie_name_access)
    assert client.cookies.get(settings.session_cookie_name_refresh)
    assert client.cookies.get(settings.session_cookie_name_csrf)

    logout = client.post("/api/v2/auth/logout", headers=csrf_headers(client))
    assert logout.status_code == 200
    assert logout.json()["message"] == "Logout realizado com sucesso"

    me_after_logout = client.get("/api/v2/auth/me")
    assert me_after_logout.status_code == 401

    events = db_session.query(SecurityAuditLog).all()
    assert len(events) >= 2


def test_auth_v2_login_rate_limit_and_audit(client, db_session):
    # Ensure this test starts with a fresh in-memory store state.
    security_store._store_cache = security_store.InMemorySecurityStore()
    create_admin(db_session, username="rate-user")

    headers = {"X-Forwarded-For": "203.0.113.10"}
    for _ in range(5):
        response = client.post(
            "/api/v2/auth/login",
            json={"username": "rate-user", "password": "wrong-password"},
            headers=headers
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v2/auth/login",
        json={"username": "rate-user", "password": "wrong-password"},
        headers=headers
    )
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "rate_limit_exceeded"

    events = db_session.query(SecurityAuditLog).filter(
        SecurityAuditLog.action == "auth_login_rate_limit"
    ).all()
    assert len(events) >= 1


def test_auth_v2_refresh_invalid_and_rate_limit_paths(client, db_session):
    security_store._store_cache = security_store.InMemorySecurityStore()
    create_admin(db_session, username="refresh-user")

    login = client.post(
        "/api/v2/auth/login",
        json={"username": "refresh-user", "password": "strong-password"}
    )
    assert login.status_code == 200

    csrf = client.cookies.get(settings.session_cookie_name_csrf)
    headers = {settings.csrf_header_name: csrf}

    # Missing refresh cookie with valid CSRF should hit "Sessao invalida" branch.
    client.cookies.pop(settings.session_cookie_name_refresh, None)
    missing_refresh = client.post("/api/v2/auth/refresh", headers=headers)
    assert missing_refresh.status_code == 401

    # Invalid refresh token branch (rotate returns None).
    client.cookies.set(settings.session_cookie_name_refresh, "invalid-refresh-token-constant")
    invalid_refresh = client.post("/api/v2/auth/refresh", headers=headers)
    assert invalid_refresh.status_code == 401

    # Rate-limit branch for refresh endpoint.
    for _ in range(9):
        response = client.post("/api/v2/auth/refresh", headers=headers)
        assert response.status_code in (401, 429)

    blocked = client.post("/api/v2/auth/refresh", headers=headers)
    assert blocked.status_code == 429
