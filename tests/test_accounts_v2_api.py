from datetime import date, timedelta

from app.config import get_settings
from app.crud import user as user_crud
from app.db.models import SecurityAuditLog
from app.schemas.user import UserCreate
from app.services import security_store

settings = get_settings()


def create_admin(db_session, username: str = "admin-v2-accounts"):
    return user_crud.create_user(
        db_session,
        UserCreate(
            username=username,
            email=f"{username}@example.com",
            password="strong-password",
            is_admin=True
        )
    )


def login_v2(client, username: str, password: str):
    response = client.post(
        "/api/v2/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response


def csrf_headers(client):
    return {settings.csrf_header_name: client.cookies.get(settings.session_cookie_name_csrf)}


def account_payload(account_number: str) -> dict:
    return {
        "account_number": account_number,
        "account_password": "plain-account-pass",
        "server": "MetaTrader",
        "buyer_name": "Buyer V2",
        "buyer_email": "buyerv2@example.com",
        "buyer_phone": "5511999999999",
        "buyer_notes": "notes",
        "purchase_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=30)),
        "purchase_price": "150.00",
        "status": "pending",
        "max_copies": 2,
        "margin_size": "2500.00",
        "phase1_target": "500.00",
        "phase1_status": "not_started",
        "phase2_target": "700.00",
        "phase2_status": None
    }


def test_admin_accounts_v2_full_flow(client, db_session):
    security_store._store_cache = security_store.InMemorySecurityStore()
    create_admin(db_session)
    login_v2(client, "admin-v2-accounts", "strong-password")

    create_resp = client.post(
        "/api/v2/admin/accounts",
        json=account_payload("ACC-V2-1"),
        headers=csrf_headers(client)
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    account_id = created["id"]
    assert "account_password" not in created

    duplicate = client.post(
        "/api/v2/admin/accounts",
        json=account_payload("ACC-V2-1"),
        headers=csrf_headers(client)
    )
    assert duplicate.status_code == 400

    second = client.post(
        "/api/v2/admin/accounts",
        json=account_payload("ACC-V2-2"),
        headers=csrf_headers(client)
    )
    second_id = second.json()["id"]

    conflict = client.put(
        f"/api/v2/admin/accounts/{second_id}",
        json={"account_number": "ACC-V2-1"},
        headers=csrf_headers(client)
    )
    assert conflict.status_code == 400

    listed = client.get("/api/v2/admin/accounts")
    assert listed.status_code == 200
    assert len(listed.json()) == 2
    assert "account_password" not in listed.json()[0]

    detail = client.get(f"/api/v2/admin/accounts/{account_id}")
    assert detail.status_code == 200
    assert "account_password" not in detail.json()

    detail_missing = client.get("/api/v2/admin/accounts/9999")
    assert detail_missing.status_code == 404

    reveal_invalid = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/reveal",
        json={"admin_password": "wrong-password"},
        headers=csrf_headers(client)
    )
    assert reveal_invalid.status_code == 401

    reveal_ok = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/reveal",
        json={"admin_password": "strong-password"},
        headers=csrf_headers(client)
    )
    assert reveal_ok.status_code == 200
    assert reveal_ok.json()["account_password"] == "plain-account-pass"
    assert reveal_ok.json()["expires_in_seconds"] == settings.password_reveal_ttl_seconds

    rotated = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/rotate",
        json={"new_password": "brand-new-password"},
        headers=csrf_headers(client)
    )
    assert rotated.status_code == 200
    assert "account_password" not in rotated.json()

    reveal_rotated = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/reveal",
        json={"admin_password": "strong-password"},
        headers=csrf_headers(client)
    )
    assert reveal_rotated.status_code == 200
    assert reveal_rotated.json()["account_password"] == "brand-new-password"

    status_changed = client.patch(
        f"/api/v2/admin/accounts/{account_id}/status",
        json={"status": "approved"},
        headers=csrf_headers(client)
    )
    assert status_changed.status_code == 200
    assert status_changed.json()["status"] == "approved"

    updated = client.put(
        f"/api/v2/admin/accounts/{account_id}",
        json={"buyer_name": "Buyer Updated"},
        headers=csrf_headers(client)
    )
    assert updated.status_code == 200
    assert updated.json()["buyer_name"] == "Buyer Updated"

    invalid_status = client.patch(
        f"/api/v2/admin/accounts/{account_id}/status",
        json={"status": "invalid_status"},
        headers=csrf_headers(client)
    )
    assert invalid_status.status_code == 400

    status_missing = client.patch(
        "/api/v2/admin/accounts/9999/status",
        json={"status": "approved"},
        headers=csrf_headers(client)
    )
    assert status_missing.status_code == 404

    update_missing = client.put(
        "/api/v2/admin/accounts/9999",
        json={"buyer_name": "Missing"},
        headers=csrf_headers(client)
    )
    assert update_missing.status_code == 404

    stats = client.get("/api/v2/admin/stats")
    assert stats.status_code == 200
    assert stats.json()["total_accounts"] == 2

    deleted = client.delete(
        f"/api/v2/admin/accounts/{account_id}",
        headers=csrf_headers(client)
    )
    assert deleted.status_code == 204

    second_deleted = client.delete(
        f"/api/v2/admin/accounts/{second_id}",
        headers=csrf_headers(client)
    )
    assert second_deleted.status_code == 204

    delete_missing = client.delete(
        "/api/v2/admin/accounts/9999",
        headers=csrf_headers(client)
    )
    assert delete_missing.status_code == 404

    security_store._store_cache = security_store.InMemorySecurityStore()
    reveal_missing = client.post(
        "/api/v2/admin/accounts/9999/password/reveal",
        json={"admin_password": "strong-password"},
        headers=csrf_headers(client)
    )
    assert reveal_missing.status_code == 404

    rotate_missing = client.post(
        "/api/v2/admin/accounts/9999/password/rotate",
        json={"new_password": "valid-password"},
        headers=csrf_headers(client)
    )
    assert rotate_missing.status_code == 404

    logs = db_session.query(SecurityAuditLog).filter(
        SecurityAuditLog.action.in_(["account_password_reveal", "account_password_rotate"])
    ).all()
    assert len(logs) >= 3


def test_admin_accounts_v2_reveal_rate_limit_and_missing_csrf(client, db_session):
    security_store._store_cache = security_store.InMemorySecurityStore()
    create_admin(db_session, username="admin-v2-rate")
    login_v2(client, "admin-v2-rate", "strong-password")

    created = client.post(
        "/api/v2/admin/accounts",
        json=account_payload("ACC-V2-RATE"),
        headers=csrf_headers(client)
    )
    account_id = created.json()["id"]

    no_csrf = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/reveal",
        json={"admin_password": "strong-password"}
    )
    assert no_csrf.status_code == 403

    for _ in range(3):
        ok = client.post(
            f"/api/v2/admin/accounts/{account_id}/password/reveal",
            json={"admin_password": "strong-password"},
            headers=csrf_headers(client)
        )
        assert ok.status_code == 200

    blocked = client.post(
        f"/api/v2/admin/accounts/{account_id}/password/reveal",
        json={"admin_password": "strong-password"},
        headers=csrf_headers(client)
    )
    assert blocked.status_code == 429


def test_admin_accounts_v2_requires_admin_role(client, db_session):
    user_crud.create_user(
        db_session,
        UserCreate(
            username="basic-v2-user",
            email="basic-v2-user@example.com",
            password="strong-password",
            is_admin=False
        )
    )
    login_v2(client, "basic-v2-user", "strong-password")
    denied = client.get("/api/v2/admin/accounts")
    assert denied.status_code == 403
